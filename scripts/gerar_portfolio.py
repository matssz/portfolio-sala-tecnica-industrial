"""Gera entregáveis leves de um portfólio técnico conceitual.

O script não dimensiona instalação real. Ele organiza os dados fornecidos em
artefatos de apresentação: DXF 2D, SVG, CSV, relatório e página para PDF.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "dados" / "equipamentos.csv"
OUTPUT = ROOT / "entregaveis"
RACK_HEIGHT_U = 42


@dataclass(frozen=True)
class Equipment:
    category: str
    item: str
    quantity: int
    rack: str
    units_u: int
    ports: int
    power_w: int
    note: str

    @property
    def total_u(self) -> int:
        return self.quantity * self.units_u

    @property
    def total_ports(self) -> int:
        return self.quantity * self.ports

    @property
    def total_power_w(self) -> int:
        return self.quantity * self.power_w


def load_equipment() -> list[Equipment]:
    with DATA_FILE.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        return [
            Equipment(
                category=row["categoria"],
                item=row["item"],
                quantity=int(row["quantidade"]),
                rack=row["rack"],
                units_u=int(row["unidades_u"]),
                ports=int(row["portas_rede"]),
                power_w=int(row["potencia_w"]),
                note=row["observacao"],
            )
            for row in reader
        ]


def summarize(items: list[Equipment]) -> dict[str, dict[str, int]]:
    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"used_u": 0, "ports": 0, "power_w": 0, "items": 0}
    )
    for item in items:
        current = totals[item.rack]
        current["used_u"] += item.total_u
        current["ports"] += item.total_ports
        current["power_w"] += item.total_power_w
        current["items"] += item.quantity

    for rack, current in totals.items():
        if current["used_u"] > RACK_HEIGHT_U:
            raise ValueError(f"{rack} excede {RACK_HEIGHT_U}U.")
    return dict(sorted(totals.items()))


def write_bom(items: list[Equipment]) -> None:
    output_file = OUTPUT / "lista_materiais.csv"
    with output_file.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(
            [
                "Categoria", "Item", "Quantidade", "Rack", "U por unidade",
                "U total", "Portas por unidade", "Portas totais",
                "Potência total estimada (W)", "Observação",
            ]
        )
        for item in items:
            writer.writerow(
                [
                    item.category, item.item, item.quantity, item.rack, item.units_u,
                    item.total_u, item.ports, item.total_ports, item.total_power_w,
                    item.note,
                ]
            )


def write_capacity_report(items: list[Equipment], summary: dict[str, dict[str, int]]) -> None:
    total_power = sum(item.total_power_w for item in items)
    total_ports = sum(item.total_ports for item in items)
    lines = [
        "# Resumo de Capacidade Conceitual",
        "",
        "> Valores apenas ilustrativos para o portfólio. Não representam dimensionamento elétrico, térmico ou de rede para implantação real.",
        "",
        "| Rack | Ocupação | Livre | Portas | Carga estimada |",
        "|---|---:|---:|---:|---:|",
    ]
    for rack, values in summary.items():
        lines.append(
            f"| {rack} | {values['used_u']}U | {RACK_HEIGHT_U - values['used_u']}U | "
            f"{values['ports']} | {values['power_w']} W |"
        )
    lines.extend(
        [
            "",
            f"**Total de portas de referência:** {total_ports}",
            f"**Carga estimada ilustrativa:** {total_power} W",
            "",
            "## Premissas",
            "",
            "- Sala conceitual de 6.000 x 4.000 mm.",
            "- Quatro racks de 42U, sem especificação de fabricante.",
            "- Rota de cabos, posicionamento e equipamentos são ilustrativos.",
            "- O projeto real dependeria de vistoria, requisitos de disponibilidade, normas, cálculo de climatização, proteção contra incêndio, elétrica, aterramento e responsabilidade técnica.",
        ]
    )
    (OUTPUT / "resumo_capacidade.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def pair(code: int, value: str | int | float) -> list[str]:
    return [str(code), str(value)]


def dxf_line(lines: list[str], layer: str, x1: int, y1: int, x2: int, y2: int, color: int = 7) -> None:
    lines.extend(pair(0, "LINE") + pair(8, layer) + pair(62, color))
    lines.extend(pair(10, x1) + pair(20, y1) + pair(30, 0))
    lines.extend(pair(11, x2) + pair(21, y2) + pair(31, 0))


def dxf_text(lines: list[str], x: int, y: int, height: int, text: str, layer: str = "TEXT", color: int = 7) -> None:
    lines.extend(pair(0, "TEXT") + pair(8, layer) + pair(62, color))
    lines.extend(pair(10, x) + pair(20, y) + pair(30, 0) + pair(40, height))
    lines.extend(pair(1, text) + pair(7, "STANDARD") + pair(50, 0))


def dxf_rect(lines: list[str], layer: str, x: int, y: int, width: int, height: int, color: int) -> None:
    dxf_line(lines, layer, x, y, x + width, y, color)
    dxf_line(lines, layer, x + width, y, x + width, y + height, color)
    dxf_line(lines, layer, x + width, y + height, x, y + height, color)
    dxf_line(lines, layer, x, y + height, x, y, color)


def write_dxf(summary: dict[str, dict[str, int]]) -> None:
    lines: list[str] = []
    lines.extend(pair(0, "SECTION") + pair(2, "HEADER") + pair(9, "$ACADVER") + pair(1, "AC1009"))
    lines.extend(pair(9, "$INSUNITS") + pair(70, 4) + pair(0, "ENDSEC"))
    lines.extend(pair(0, "SECTION") + pair(2, "TABLES") + pair(0, "TABLE") + pair(2, "LAYER") + pair(70, 5))
    for layer, color in [("0", 7), ("WALL", 7), ("RACK", 3), ("CABLE", 1), ("TEXT", 7)]:
        lines.extend(pair(0, "LAYER") + pair(2, layer) + pair(70, 0) + pair(62, color) + pair(6, "CONTINUOUS"))
    lines.extend(pair(0, "ENDTAB") + pair(0, "ENDSEC") + pair(0, "SECTION") + pair(2, "ENTITIES"))

    # Sala em milímetros: 6.000 x 4.000. Esta representação é somente visual.
    dxf_rect(lines, "WALL", 0, 0, 6000, 4000, 7)
    dxf_text(lines, 0, 4250, 210, "SALA TECNICA INDUSTRIAL - PROJETO CONCEITUAL", "TEXT", 7)
    dxf_text(lines, 0, 4020, 110, "PLANTA 2D | 6000 x 4000 mm | NAO EXECUTAR", "TEXT", 1)

    # Corredor frio conceitual e rota superior de cabos.
    dxf_rect(lines, "CABLE", 450, 1600, 5100, 700, 1)
    dxf_text(lines, 2100, 1900, 100, "CORREDOR TECNICO / ACESSO", "TEXT", 1)
    dxf_line(lines, "CABLE", 350, 3470, 5650, 3470, 1)
    dxf_text(lines, 2100, 3560, 100, "ROTA CONCEITUAL DE CABOS", "TEXT", 1)

    positions = {"R01": 600, "R02": 1900, "R03": 3200, "R04": 4500}
    for rack, x in positions.items():
        dxf_rect(lines, "RACK", x, 2500, 700, 900, 3)
        values = summary[rack]
        dxf_text(lines, x + 175, 2980, 140, rack, "TEXT", 3)
        dxf_text(lines, x + 85, 2780, 90, f"{values['used_u']}U / 42U", "TEXT", 7)
        dxf_text(lines, x + 85, 2640, 90, f"{values['ports']} portas", "TEXT", 7)
        dxf_text(lines, x + 85, 2510, 90, f"{values['power_w']} W est.", "TEXT", 7)

    dxf_rect(lines, "WALL", 400, 300, 1100, 700, 7)
    dxf_text(lines, 580, 680, 120, "AREA DE MANUTENCAO", "TEXT", 7)
    dxf_rect(lines, "WALL", 4300, 300, 1200, 700, 7)
    dxf_text(lines, 4510, 680, 120, "ENTRADA TECNICA", "TEXT", 7)
    dxf_text(lines, 0, -450, 100, "Notas: valores, layout e equipamentos sao apenas ilustrativos para portfolio.", "TEXT", 7)
    lines.extend(pair(0, "ENDSEC") + pair(0, "EOF"))
    (OUTPUT / "planta_conceitual.dxf").write_text("\n".join(lines) + "\n", encoding="ascii")


def write_svg(summary: dict[str, dict[str, int]]) -> None:
    racks = []
    for rack, x in [("R01", 110), ("R02", 310), ("R03", 510), ("R04", 710)]:
        values = summary[rack]
        racks.append(
            f'<g><rect x="{x}" y="125" width="115" height="150" rx="7" class="rack"/>'
            f'<text x="{x + 57}" y="170" class="rack-id">{rack}</text>'
            f'<text x="{x + 57}" y="195" class="rack-detail">{values["used_u"]}U / 42U</text>'
            f'<text x="{x + 57}" y="216" class="rack-detail">{values["ports"]} portas</text>'
            f'<text x="{x + 57}" y="237" class="rack-detail">{values["power_w"]} W est.</text></g>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620" viewBox="0 0 1000 620">
<style>
  .bg {{ fill: #f6f3ea; }} .room {{ fill: #fffdf8; stroke: #193d38; stroke-width: 4; }}
  .aisle {{ fill: #d8efe8; stroke: #16877f; stroke-width: 2; }} .rack {{ fill: #e8bf68; stroke: #193d38; stroke-width: 2; }}
  .route {{ stroke: #cc6b50; stroke-width: 5; stroke-dasharray: 11 8; }}
  text {{ font-family: Arial, sans-serif; fill: #193d38; }} .title {{ font-size: 27px; font-weight: 700; }}
  .subtitle {{ font-size: 15px; fill: #49645e; }} .rack-id {{ font-size: 18px; font-weight: 700; text-anchor: middle; }}
  .rack-detail {{ font-size: 12px; text-anchor: middle; fill: #49645e; }} .label {{ font-size: 15px; font-weight: 700; }}
</style>
<rect class="bg" width="1000" height="620"/>
<text class="title" x="50" y="48">Sala Tecnica Industrial de Borda</text>
<text class="subtitle" x="50" y="76">Projeto conceitual de portfólio | Planta 2D | Não executar</text>
<rect class="room" x="50" y="105" width="900" height="400" rx="6"/>
<line class="route" x1="100" y1="145" x2="900" y2="145"/>
<text class="subtitle" x="390" y="132">ROTA CONCEITUAL DE CABOS</text>
<rect class="aisle" x="90" y="315" width="820" height="75" rx="5"/>
<text class="label" x="358" y="360">CORREDOR TECNICO / ACESSO</text>
{''.join(racks)}
<rect class="room" x="105" y="425" width="180" height="55"/><text class="label" x="125" y="458">AREA DE MANUTENCAO</text>
<rect class="room" x="700" y="425" width="180" height="55"/><text class="label" x="723" y="458">ENTRADA TECNICA</text>
<text class="subtitle" x="50" y="560">Premissas e cargas são ilustrativas. Projeto real exige vistoria, normas e responsável técnico.</text>
</svg>'''
    (OUTPUT / "planta_conceitual.svg").write_text(svg, encoding="utf-8")


def write_presentation(items: list[Equipment], summary: dict[str, dict[str, int]]) -> None:
    total_power = sum(item.total_power_w for item in items)
    total_ports = sum(item.total_ports for item in items)
    rows = "".join(
        f"<tr><td>{escape(rack)}</td><td>{values['used_u']}U / 42U</td><td>{RACK_HEIGHT_U - values['used_u']}U</td><td>{values['ports']}</td><td>{values['power_w']} W</td></tr>"
        for rack, values in summary.items()
    )
    html = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Portfólio | Sala Técnica Industrial de Borda</title>
<style>
@page {{ size: A4; margin: 13mm; }}
* {{ box-sizing: border-box; }} body {{ margin: 0; color: #173d37; background: #f6f3ea; font: 14px Arial, sans-serif; }}
.page {{ max-width: 900px; margin: 0 auto; padding: 42px; background: #fffdf8; }} .eyebrow {{ color: #16877f; font-size: 11px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase; }}
h1 {{ max-width: 700px; margin: 12px 0 8px; font-size: 35px; line-height: 1.03; }} h2 {{ margin: 29px 0 10px; font-size: 20px; }}
p, li {{ color: #45625c; line-height: 1.55; }} .notice {{ border-left: 4px solid #cc6b50; padding: 11px 14px; background: #fff0ea; color: #7f4234; }}
.metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 22px 0; }} .metric {{ padding: 15px; border-radius: 10px; background: #d8efe8; }} .metric b {{ display: block; font-size: 25px; }} .metric span {{ font-size: 11px; font-weight: 700; }}
img {{ width: 100%; margin: 16px 0 5px; border: 1px solid #cbded8; border-radius: 10px; }} table {{ width: 100%; border-collapse: collapse; font-size: 12px; }} th {{ color: white; background: #173d37; text-align: left; }} td, th {{ padding: 9px; border-bottom: 1px solid #d8e4e0; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }} footer {{ margin-top: 30px; padding-top: 12px; border-top: 1px solid #d8e4e0; color: #617a74; font-size: 10px; }}
</style></head><body><main class="page">
<span class="eyebrow">Projeto conceitual de portfólio</span><h1>Sala Técnica Industrial de Borda</h1><p>Documentação 2D, inventário técnico e automação leve para uma implantação conceitual em ambiente industrial.</p>
<p class="notice"><b>Limite do material:</b> não é projeto executivo, memorial de cálculo, especificação de fabricante ou orientação para obra. Os números e posicionamentos existem apenas para demonstrar método de organização e documentação.</p>
<section class="metrics"><div class="metric"><b>4</b><span>RACKS CONCEITUAIS</span></div><div class="metric"><b>{total_ports}</b><span>PORTAS DE REFERÊNCIA</span></div><div class="metric"><b>{total_power} W</b><span>CARGA ILUSTRATIVA</span></div></section>
<h2>Entregáveis</h2><div class="two"><div><ul><li>Planta geral da sala em 2D.</li><li>Posicionamento de racks e corredor técnico.</li><li>Rota conceitual de cabeamento.</li></ul></div><div><ul><li>Lista de equipamentos rastreável.</li><li>Ocupação de rack, portas e carga.</li><li>DXF editável e prévia vetorial.</li></ul></div></div>
<img src="planta_conceitual.svg" alt="Planta conceitual da sala técnica">
<h2>Resumo de capacidade</h2><table><thead><tr><th>Rack</th><th>Ocupação</th><th>Livre</th><th>Portas</th><th>Carga estimada</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Método demonstrado</h2><p>O inventário é mantido em CSV. Um script Python valida a ocupação de 42U por rack e gera automaticamente a lista de materiais, o resumo de capacidade, a planta DXF, a prévia SVG e esta página. Assim, alteração de dados pode ser refletida nos entregáveis sem recálculo manual.</p>
<footer>Portfólio autoral para entrevista. Para implantação real: vistoria, requisitos, normas, cálculos e aprovação de profissionais habilitados.</footer>
</main></body></html>'''
    (OUTPUT / "apresentacao.html").write_text(html, encoding="utf-8")


def write_interview_script() -> None:
    text = """# Roteiro para Entrevista

## Abertura em 40 segundos

"Preparei este projeto conceitual para demonstrar como eu organizo uma entrega técnica. Modelei uma sala técnica industrial de borda com planta 2D, racks, rota conceitual de cabos e inventário. Mantive os dados em uma planilha CSV e usei Python para consolidar ocupação de rack, portas e carga ilustrativa. Assim, quis mostrar AutoCAD, organização, rastreabilidade e automação, sem afirmar que se trata de um projeto executivo ou homologado."

## Como explicar o AutoCAD

"No desenho, eu começo por unidades, layers e padrão de anotação. Uso elementos repetitivos como blocos e mantenho a organização por disciplina: arquitetura, racks, rota de cabos e textos. A entrega final precisa ter layout, escala, carimbo, revisão e PDF controlado. Antes de entregar, reviso referências, escalas e informações que precisam bater com a lista de equipamentos."

## Se perguntarem sobre os números

"Os valores foram definidos como premissas didáticas para o portfólio. Em um projeto real, eu levantaria requisitos do cliente, disponibilidade necessária, potência, climatização, cabeamento, aterramento, prevenção contra incêndio, normas aplicáveis e validação com profissionais responsáveis."

## O que não afirmar

- Não diga que este é um projeto Huawei ou que usa especificação oficial da Huawei.
- Não diga que o desenho está pronto para obra.
- Não invente domínio de recursos do AutoCAD que você não usou.

## Perguntas para a equipe

1. A equipe entrega mais estudo preliminar, executivo, as-built ou documentação de implantação?
2. Quais padrões de layers, revisão e controle documental são usados pela área?
3. Como projeto, campo, fornecedores e cliente validam mudanças?
4. Quais ferramentas de desenho e gestão são mais importantes para a posição?
"""
    (OUTPUT / "roteiro_entrevista.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    items = load_equipment()
    summary = summarize(items)
    write_bom(items)
    write_capacity_report(items, summary)
    write_dxf(summary)
    write_svg(summary)
    write_presentation(items, summary)
    write_interview_script()
    print("Entregáveis gerados em:", OUTPUT)


if __name__ == "__main__":
    main()
