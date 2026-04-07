# Negative Momentum Method

## Documentação em pt-BR

Este repositório é um fork/adaptação de um projeto associado ao artigo aceito na AAAI 2025: [Rapid Learning in Constrained Minimax Games with Negative Momentum](https://arxiv.org/abs/2501.00533). O objetivo do código é explorar métodos de aprendizado rápido em jogos minimax com restrições, com ênfase em técnicas baseadas em momento negativo.

O projeto reúne implementações e experimentos voltados para jogos de soma zero, especialmente jogos sequenciais com informação imperfeita, como Kuhn Poker e Leduc Poker. A base experimental usa algoritmos de regret minimization e métodos em forma sequencial para avaliar convergência e exploitability.

### Principais componentes

- `NM-Method/MoCFR.py`: implementação modificada de CFR/CFR+, incorporando uma ideia de momento negativo no acúmulo de arrependimentos.
- `NM-Method/CFR_run.py`: script de execução para experimentos com CFR/MoCFR usando OpenSpiel.
- `NM-Method/sequence_form_run.py`: script principal para experimentos em forma sequencial, com variantes como MMD, OMWU, OGDA, GDA, MoMMWU e MoGDA.
- `NM-Method/sequence_form_utils.py`: utilitários para construção e conversão de representações em forma sequencial.
- `NM-Method/sequence_form_algo/`: implementações dos algoritmos em forma sequencial.
- `NM-Method/kuhnEx.py`: experimento autocontido com Kuhn Poker expandido.
- `NM-Method/leduc_exp.py`: experimento autocontido com uma versão simplificada de Leduc Poker.
- `NM-Method/mini_mocfr.py` e `NM-Method/mini_mocfr_two_players.py`: exemplos menores para estudar o comportamento do MoCFR em cenários simples.

### Aplicação visual separada

Além dos arquivos de pesquisa, o repositório inclui uma aplicação separada em `apps/`:

- `apps/backend/`: API em Python/FastAPI para simular Kuhn Poker com CFR e momento negativo.
- `apps/frontend/`: interface React/Vite para visualizar cartas, parâmetros de treinamento, curva de exploitability e estratégia aprendida.

Essa separação evita misturar a camada de produto com os arquivos originais da solução do paper. A aplicação visual usa, no modo didático, a adaptação `NM-Method/Kuhn_Poker_CFR-style_MoCFR.py` por meio de `apps/backend/kuhn_service.py`. Ela também oferece um modo opcional chamado `Paper fork`, que chama `NM-Method/MoCFR.py` por meio de `apps/backend/paper_bridge.py`, sem alterar os arquivos originais de pesquisa.

### Dependências

O projeto usa Python e depende de bibliotecas científicas e de experimentação, incluindo:

- `numpy`
- `scipy`
- `matplotlib`
- `absl-py`
- `open_spiel` / `pyspiel`
- `wandb`, quando o rastreamento de experimentos estiver habilitado

Observação: o arquivo `NM-Method/requirements.txt` foi ajustado para usar versões instaláveis via PyPI, evitando referências a wheels locais de Termux/Android.

Para Debian ARM64 rodando dentro do Termux no Android, use `NM-Method/requirements-arm64.txt`. Esse arquivo evita wheels locais e usa `uvicorn` sem o extra `standard`, reduzindo a chance de falhas com dependências nativas em ambientes `proot`.

### Execução

Alguns scripts podem ser executados diretamente, dependendo das dependências disponíveis no ambiente.

Exemplo com experimento simplificado:

```bash
python3 NM-Method/mini_mocfr.py
```

Exemplo com Kuhn Poker expandido:

```bash
python3 NM-Method/kuhnEx.py
```

Exemplo com métodos em forma sequencial usando OpenSpiel:

```bash
python3 NM-Method/sequence_form_run.py --iterations=10000 --print_freq=10
```

Exemplo com MoCFR usando OpenSpiel:

```bash
python3 NM-Method/CFR_run.py
```

Exemplo com a aplicação visual separada:

```bash
./install.sh
./start.sh
```

Em ARM64/Termux-Debian, o instalador detecta a arquitetura e oferece o uso de `requirements-arm64.txt`.

Se preferir iniciar os serviços manualmente, execute o backend:

```bash
source .venv/bin/activate
cd apps/backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

E, em outro terminal, execute o frontend:

```bash
cd apps/frontend
npm run dev
```

Para registrar métricas no Weights & Biases, use a flag `--use_wandb=True` nos scripts que oferecem esse suporte e configure o projeto com `--project_name`.

### Estado do projeto

Este repositório tem caráter experimental. Alguns arquivos são scripts de pesquisa, com parâmetros fixados diretamente no código e alternativas comentadas para outros jogos. O arquivo `NM-Method/Reg_method.py` referencia dependências que podem não estar presentes neste repositório, como `LiteEFG` e módulos `*_moving`, portanto esse script pode exigir código externo ou ajustes adicionais para execução.

## English Documentation

This repository is a fork/adaptation of a project associated with the AAAI 2025 accepted paper: [Rapid Learning in Constrained Minimax Games with Negative Momentum](https://arxiv.org/abs/2501.00533). The code explores rapid learning methods for constrained minimax games, with an emphasis on negative momentum techniques.

The project contains implementations and experiments for zero-sum games, especially sequential imperfect-information games such as Kuhn Poker and Leduc Poker. The experimental code combines regret minimization algorithms and sequence-form methods to evaluate convergence and exploitability.

### Main Components

- `NM-Method/MoCFR.py`: modified CFR/CFR+ implementation that incorporates a negative momentum idea into regret accumulation.
- `NM-Method/CFR_run.py`: runner script for CFR/MoCFR experiments using OpenSpiel.
- `NM-Method/sequence_form_run.py`: main runner for sequence-form experiments, including variants such as MMD, OMWU, OGDA, GDA, MoMMWU, and MoGDA.
- `NM-Method/sequence_form_utils.py`: utilities for constructing and converting sequence-form representations.
- `NM-Method/sequence_form_algo/`: implementations of the sequence-form algorithms.
- `NM-Method/kuhnEx.py`: self-contained experiment for expanded Kuhn Poker.
- `NM-Method/leduc_exp.py`: self-contained experiment for a simplified Leduc Poker setting.
- `NM-Method/mini_mocfr.py` and `NM-Method/mini_mocfr_two_players.py`: smaller examples for studying MoCFR behavior in simple settings.

### Separate Visual Application

In addition to the research files, the repository includes a separate application under `apps/`:

- `apps/backend/`: Python/FastAPI API for simulating Kuhn Poker with CFR and negative momentum.
- `apps/frontend/`: React/Vite interface for visualizing cards, training parameters, the exploitability curve, and the learned strategy.

This separation avoids mixing the product layer with the original paper solution files. In educational mode, the visual application uses the `NM-Method/Kuhn_Poker_CFR-style_MoCFR.py` adaptation through `apps/backend/kuhn_service.py`. It also provides an optional `Paper fork` mode that calls `NM-Method/MoCFR.py` through `apps/backend/paper_bridge.py`, without modifying the original research files.

### Dependencies

The project uses Python and depends on scientific computing and experimentation libraries, including:

- `numpy`
- `scipy`
- `matplotlib`
- `absl-py`
- `open_spiel` / `pyspiel`
- `wandb`, when experiment tracking is enabled

Note: `NM-Method/requirements.txt` was adjusted to use PyPI-installable versions, avoiding references to local Termux/Android wheel files.

For Debian ARM64 running inside Termux on Android, use `NM-Method/requirements-arm64.txt`. This file avoids local wheels and uses `uvicorn` without the `standard` extra, reducing the chance of native dependency failures in `proot` environments.

### Running

Some scripts can be executed directly, depending on the dependencies available in the environment.

Simplified experiment:

```bash
python3 NM-Method/mini_mocfr.py
```

Expanded Kuhn Poker experiment:

```bash
python3 NM-Method/kuhnEx.py
```

Sequence-form methods using OpenSpiel:

```bash
python3 NM-Method/sequence_form_run.py --iterations=10000 --print_freq=10
```

MoCFR using OpenSpiel:

```bash
python3 NM-Method/CFR_run.py
```

Separate visual application:

```bash
./install.sh
./start.sh
```

On ARM64/Termux-Debian, the installer detects the architecture and offers `requirements-arm64.txt`.

If you prefer to start the services manually, run the backend:

```bash
source .venv/bin/activate
cd apps/backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then, in another terminal, run the frontend:

```bash
cd apps/frontend
npm run dev
```

To log metrics to Weights & Biases, use the `--use_wandb=True` flag in scripts that support it and configure the project with `--project_name`.

### Project Status

This repository is experimental. Some files are research scripts, with parameters hardcoded directly in the source and commented alternatives for other games. The `NM-Method/Reg_method.py` file references dependencies that may not be present in this repository, such as `LiteEFG` and `*_moving` modules, so that script may require external code or additional adjustments before it can run.
