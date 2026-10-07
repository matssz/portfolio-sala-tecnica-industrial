# Decisões de Projeto

## 1. Cenário escolhido

Foi escolhida uma sala técnica industrial de borda porque ela permite relacionar infraestrutura física, rede, energia, automação e documentação em um único exercício. O cenário é pequeno o suficiente para ser explicado em poucos minutos, mas contém interfaces que aparecem em projetos profissionais.

## 2. Escopo intencionalmente limitado

O projeto contém layout, racks, rota conceitual de cabos, inventário e quantitativos ilustrativos. Ele não contém cálculo elétrico, climatização, aterramento, proteção contra incêndio, esforço estrutural, seleção de produto, orçamento real ou aprovação normativa.

Essa separação é importante: um portfólio técnico deve demonstrar competência sem apresentar uma simulação como se fosse uma solução pronta para obra.

## 3. Premissas de layout

| Premissa | Motivo didático |
|---|---|
| Sala de 6.000 x 4.000 mm | Escala suficiente para visualizar equipamentos e circulação. |
| Quatro racks de 42U | Permite mostrar inventário por função e controle de ocupação. |
| Corredor técnico | Destaca manutenção, acesso e organização operacional. |
| Rota superior de cabos | Demonstra interface entre layout e conectividade. |
| Camadas separadas | Ajuda a manter o desenho legível e editável. |

## 4. Rastreabilidade de dados

O arquivo `dados/equipamentos.csv` é a fonte única de verdade do exercício. Toda mudança deve começar nele. O script gera os demais artefatos a partir dessa base, reduzindo divergências entre desenho, lista e apresentação.

Exemplo: se a quantidade de servidores no rack `R02` for alterada, o script recalcula o total de unidades de rack, portas e potência ilustrativa do rack antes de escrever o relatório.

## 5. Padrão de desenho usado no DXF

O DXF utiliza as camadas abaixo para tornar a intenção visual clara:

| Camada | Uso |
|---|---|
| `WALL` | Limites da sala, manutenção e entrada técnica. |
| `RACK` | Racks e identificação operacional. |
| `CABLE` | Corredor e rota conceitual de cabeamento. |
| `TEXT` | Títulos, notas e anotações. |

Em um projeto real, o padrão seria acordado com o cliente e poderia incluir carimbo, escalas, Xrefs, blocos com atributos, revisão e convenções por disciplina.

## 6. Verificações automatizadas

O script interrompe a geração se algum rack ultrapassar 42U. Esta regra é simples, mas ilustra um princípio de qualidade: verificações repetitivas devem ser executadas por código sempre que possível.

## 7. Evoluções possíveis

- Gerar blocos com atributos para cada equipamento no DXF.
- Integrar o inventário a uma planilha XLSX.
- Criar uma topologia lógica de rede em SVG.
- Adicionar testes automatizados para os cálculos.
- Criar uma versão em inglês para envio internacional.
