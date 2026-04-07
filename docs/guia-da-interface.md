# Guia da interface visual

Este documento explica a interface visual do projeto em termos de funcionalidade da página. A ideia é ajudar quem chega de fora do projeto a entender o que cada parte da tela faz, sem precisar conhecer o código do frontend.

## Visão geral

A página é uma interface visual para acompanhar um treinamento de Kuhn Poker usando o método de Negative Momentum. Em vez de exigir que o usuário rode scripts no terminal e interprete números crus, a tela transforma o experimento em uma simulação acompanhável.

Pela interface, o usuário pode escolher parâmetros, iniciar o treinamento, acompanhar a curva de convergência e inspecionar a estratégia aprendida por carta e jogador.

## Topo da página

No topo, a página apresenta o contexto do experimento com o nome **Negative Momentum Method** e o título **Kuhn Poker em tempo real**.

Essa área explica a proposta principal da tela: mostrar o treinamento avançando por checkpoints, acompanhar a queda da exploitability e permitir a inspeção da estratégia aprendida.

Também existe um cartão de métrica com a **iteração atual**. Ele mostra em que ponto do treinamento a simulação está, por exemplo:

```text
Iteração
500
de 2000
```

Na prática, esse cartão funciona como um contador visual do progresso do treinamento.

## Painel de configuração

Na lateral esquerda fica o painel em que o usuário controla a simulação.

A primeira escolha é o **modo da simulação**:

- **Didático**: usa a implementação adaptada para a aplicação visual. É o modo principal da interface, pensado para mostrar os resultados de forma mais direta.
- **Paper fork**: usa a implementação baseada no código do paper, quando as dependências necessárias estão disponíveis no ambiente.

Abaixo da escolha de modo, a página mostra uma mensagem explicando qual fonte está sendo usada. Se o modo `Paper fork` não estiver disponível, a interface informa isso e mostra o motivo.

Depois aparecem os parâmetros do treinamento:

- **Iterações**: define quantas rodadas de treinamento serão executadas. Quanto maior o número, mais tempo o algoritmo tem para ajustar a estratégia.
- **Momento negativo**: controla a intensidade do parâmetro de negative momentum usado no treinamento.
- **Intervalo de referência**: define de quanto em quanto tempo o sistema coleta checkpoints para atualizar o gráfico e a lista de passos.
- **Semente**: controla a repetibilidade do experimento. Usar a mesma semente ajuda a comparar resultados entre execuções.

Também há um controle de **velocidade dos checkpoints**. Ele ajusta o intervalo visual entre uma atualização e outra:

- Com valor `0`, a simulação aparece praticamente de forma instantânea.
- Com valores maiores, a página mostra os checkpoints mais devagar, como uma animação do treinamento acontecendo.

Por fim, o botão **Rodar treinamento** inicia a simulação. Enquanto o treinamento está em execução, ele muda para **Treinando...**. Se ocorrer algum problema, a mensagem de erro aparece logo abaixo.

## Painel de monitoramento

A área principal da página mostra o estado atual do treinamento.

No topo desse painel existem três indicadores:

- **Exploitability**: mostra o valor final ou mais recente da exploitability. Em termos simples, quanto menor esse número, melhor a estratégia está se aproximando de um equilíbrio.
- **Fonte**: indica se os dados vêm do modo **Didático** ou do **Paper fork**.
- **Status**: mostra se a simulação está pronta, em tempo real ou com erro.

Logo abaixo existe uma **barra de progresso**. Ela cresce conforme o treinamento avança e ajuda o usuário a perceber quanto da simulação já foi concluído.

## Gráfico de convergência

O gráfico chamado **Convergência** mostra a evolução da exploitability ao longo das iterações.

Cada ponto no gráfico representa um checkpoint emitido pelo backend. Por exemplo, se o treinamento tem 2000 iterações e os checkpoints são emitidos ao longo do processo, a página mostra pontos intermediários até chegar ao resultado final.

A linha do gráfico ajuda o usuário a perceber se o treinamento está melhorando. O comportamento esperado é a exploitability diminuir com o tempo, indicando que a estratégia está ficando menos explorável.

O gráfico também destaca o ponto mais recente, mostrando a iteração atual e o valor de exploitability naquele momento, por exemplo:

```text
Iter 2000 - 0.023451
```

## Passos do treinamento

A seção **Passos do treinamento** lista os checkpoints em formato de histórico.

Cada item mostra:

- a iteração;
- o valor de exploitability naquela iteração.

Na prática, essa seção é uma versão textual do gráfico. Ela é útil para quem quer ver os valores exatos checkpoint por checkpoint, sem depender apenas da curva visual.

Exemplo:

```text
Iteração 1       0.875000
Iteração 200     0.213421
Iteração 400     0.098120
```

## Estratégia aprendida

A seção **Estratégia aprendida** permite explorar o resultado do treinamento de forma mais interpretável.

O usuário pode escolher:

- qual jogador analisar: **Jogador 1** ou **Jogador 2**;
- qual carta esse jogador tem: **J**, **Q** ou **K**.

No Kuhn Poker, as cartas podem ser entendidas assim:

- **J**: carta mais fraca;
- **Q**: carta intermediária;
- **K**: carta mais forte.

Depois de escolher jogador e carta, a página mostra as decisões disponíveis para aquela situação.

Cada decisão aparece com um contexto, por exemplo:

- **Início**: decisão inicial;
- **Check**: depois de alguém dar check;
- **Bet**: depois de alguém apostar;
- **Check, Bet**: depois de check seguido de aposta.

Para cada contexto, a página mostra a **ação recomendada** e duas barras de probabilidade:

- **Check/Call**: chance de o jogador passar ou pagar;
- **Bet/Raise**: chance de o jogador apostar ou aumentar.

Por exemplo:

```text
Check/Call 80%
Bet/Raise 20%
```

Isso significa que, naquela situação específica, a estratégia aprendida prefere passar ou pagar na maior parte das vezes, mas ainda aposta ou aumenta em uma pequena porcentagem das vezes.

Esse comportamento é importante porque estratégias em jogos como poker nem sempre devem ser determinísticas. Uma boa estratégia pode precisar misturar ações para não ficar previsível.

## Fluxo de uso

O uso normal da página segue este caminho:

1. Escolher o modo da simulação.
2. Ajustar iterações, momento negativo, intervalo, semente e velocidade.
3. Clicar em **Rodar treinamento**.
4. Acompanhar a exploitability no painel e no gráfico.
5. Ver os checkpoints na lista de passos.
6. Explorar a estratégia final por jogador e por carta.

Em resumo, a página funciona como um painel interativo para transformar o treinamento de um algoritmo de poker em algo visual e compreensível. Ela mostra tanto o desempenho geral do treinamento quanto o comportamento estratégico aprendido em situações específicas do jogo.
