#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_DIR="$ROOT_DIR/NM-Method"
REQUIREMENTS_FILE="$PYTHON_DIR/requirements.txt"
ARM64_REQUIREMENTS_FILE="$PYTHON_DIR/requirements-arm64.txt"
BACKEND_REQUIREMENTS_FILE="$ROOT_DIR/apps/backend/requirements.txt"
BACKEND_ARM64_REQUIREMENTS_FILE="$ROOT_DIR/apps/backend/requirements-arm64.txt"
VENV_DIR="$ROOT_DIR/.venv"
DEFAULT_FRONTEND_DIR="$ROOT_DIR/apps/frontend"

print_header() {
  printf "\n==> %s\n" "$1"
}

print_info() {
  printf "    %s\n" "$1"
}

ask_yes_no() {
  local prompt="$1"
  local default="${2:-n}"
  local suffix
  local answer

  if [[ "$default" == "y" ]]; then
    suffix="[S/n]"
  else
    suffix="[s/N]"
  fi

  while true; do
    read -r -p "$prompt $suffix " answer
    answer="${answer:-$default}"
    case "${answer,,}" in
      s|sim|y|yes) return 0 ;;
      n|nao|não|no) return 1 ;;
      *) printf "Responda com sim ou nao.\n" ;;
    esac
  done
}

ask_text() {
  local prompt="$1"
  local default="$2"
  local answer

  read -r -p "$prompt [$default] " answer
  printf "%s" "${answer:-$default}"
}

require_command() {
  local command_name="$1"
  local install_hint="$2"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf "Comando obrigatorio nao encontrado: %s\n" "$command_name" >&2
    printf "Instale-o antes de continuar. Sugestao: %s\n" "$install_hint" >&2
    exit 1
  fi
}

detect_architecture() {
  uname -m
}

is_arm64_architecture() {
  local architecture="$1"

  case "$architecture" in
    aarch64|arm64) return 0 ;;
    *) return 1 ;;
  esac
}

select_python() {
  if command -v python3 >/dev/null 2>&1; then
    printf "python3"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    printf "python"
    return 0
  fi

  printf "Python nao encontrado. Instale Python 3 antes de continuar.\n" >&2
  exit 1
}

install_python_environment() {
  local python_bin="$1"
  local architecture="$2"
  local pip_bin="$VENV_DIR/bin/pip"
  local python_venv_bin="$VENV_DIR/bin/python"
  local selected_requirements="$REQUIREMENTS_FILE"
  local selected_backend_requirements="$BACKEND_REQUIREMENTS_FILE"
  local tmp_requirements

  print_header "Ambiente Python"
  print_info "Python detectado: $($python_bin --version)"
  print_info "Arquitetura detectada: $architecture"

  if is_arm64_architecture "$architecture"; then
    print_info "Ambiente ARM64 detectado."
    if [[ -f "$ARM64_REQUIREMENTS_FILE" ]] && ask_yes_no "Deseja usar requirements-arm64.txt para maior compatibilidade?" "y"; then
      selected_requirements="$ARM64_REQUIREMENTS_FILE"
    fi

    if [[ -f "$BACKEND_ARM64_REQUIREMENTS_FILE" ]]; then
      selected_backend_requirements="$BACKEND_ARM64_REQUIREMENTS_FILE"
    fi
  fi

  if [[ -d "$VENV_DIR" ]]; then
    print_info "Ambiente virtual ja existe em: $VENV_DIR"
    if ask_yes_no "Deseja recriar o ambiente virtual Python?" "n"; then
      rm -rf "$VENV_DIR"
      "$python_bin" -m venv "$VENV_DIR"
    fi
  else
    if ask_yes_no "Deseja criar o ambiente virtual Python em .venv?" "y"; then
      "$python_bin" -m venv "$VENV_DIR"
    else
      print_info "Criacao do ambiente Python ignorada."
      return 0
    fi
  fi

  if [[ ! -x "$python_venv_bin" ]]; then
    printf "Ambiente virtual invalido ou incompleto: %s\n" "$VENV_DIR" >&2
    exit 1
  fi

  "$python_venv_bin" -m pip install --upgrade pip setuptools wheel

  if [[ ! -f "$selected_requirements" ]]; then
    print_info "Arquivo de requirements nao encontrado em: $selected_requirements"
    return 0
  fi

  if ask_yes_no "Deseja instalar as dependencias Python de '$selected_requirements'?" "y"; then
    if grep -q " @ file://" "$selected_requirements"; then
      print_info "Foram encontradas dependencias apontando para wheels locais."
      print_info "Sera criado um requirements temporario substituindo essas linhas por pacotes PyPI."
      tmp_requirements="$(mktemp)"
      sed -E 's/^([A-Za-z0-9_.-]+)[[:space:]]+@ file:.*/\1/' "$selected_requirements" > "$tmp_requirements"
      "$pip_bin" install -r "$tmp_requirements"
      rm -f "$tmp_requirements"
    else
      "$pip_bin" install -r "$selected_requirements"
    fi
  fi

  if ask_yes_no "Deseja instalar dependencias extras usadas por alguns scripts (open_spiel, wandb, attrs e tqdm)?" "n"; then
    if is_arm64_architecture "$architecture"; then
      print_info "Aviso: open_spiel pode falhar em Termux/Debian/proot se nao houver wheel compativel."
    fi
    "$pip_bin" install open_spiel wandb attrs tqdm
  fi

  if [[ -f "$selected_backend_requirements" ]] && ask_yes_no "Deseja instalar as dependencias da API em apps/backend?" "y"; then
    "$pip_bin" install -r "$selected_backend_requirements"
  fi

  print_info "Para ativar o ambiente depois: source .venv/bin/activate"
  print_info "Para executar a API: cd apps/backend && ../../.venv/bin/python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
}

find_package_json_dirs() {
  find "$ROOT_DIR" \
    -path "$ROOT_DIR/node_modules" -prune -o \
    -path "$ROOT_DIR/.venv" -prune -o \
    -name package.json -type f -print |
    sed 's#/package.json$##'
}

install_node_environment() {
  local package_dirs
  local frontend_dir

  print_header "Ambiente Node/React"

  if ! command -v node >/dev/null 2>&1; then
    print_info "Node.js nao foi encontrado. Instale Node.js LTS antes de configurar o ambiente React."
    return 0
  fi

  if ! command -v npm >/dev/null 2>&1; then
    print_info "npm nao foi encontrado. Instale npm antes de configurar o ambiente React."
    return 0
  fi

  print_info "Node detectado: $(node --version)"
  print_info "npm detectado: $(npm --version)"

  package_dirs="$(find_package_json_dirs || true)"

  if [[ -n "$package_dirs" ]]; then
    print_info "Projetos Node encontrados:"
    printf "%s\n" "$package_dirs" | sed 's/^/    - /'

    while IFS= read -r package_dir; do
      [[ -z "$package_dir" ]] && continue
      if ask_yes_no "Deseja instalar as dependencias Node em '$package_dir'?" "y"; then
        if [[ -f "$package_dir/package-lock.json" ]]; then
          (cd "$package_dir" && npm ci)
        else
          (cd "$package_dir" && npm install)
        fi
      fi
    done <<< "$package_dirs"
  else
    print_info "Nenhum package.json foi encontrado neste repositorio."
    if ask_yes_no "Deseja criar um frontend React com Vite?" "n"; then
      frontend_dir="$(ask_text "Diretorio do frontend" "$DEFAULT_FRONTEND_DIR")"
      if [[ -e "$frontend_dir" ]]; then
        printf "O caminho ja existe: %s\n" "$frontend_dir" >&2
        printf "Remova-o ou escolha outro diretorio ao executar novamente.\n" >&2
        exit 1
      fi
      npm create vite@latest "$frontend_dir" -- --template react
      (cd "$frontend_dir" && npm install)
      print_info "Frontend React criado em: $frontend_dir"
      print_info "Para executar: cd '$frontend_dir' && npm run dev"
    else
      print_info "Criacao do frontend React ignorada."
    fi
  fi
}

main() {
  local architecture
  local python_bin

  print_header "Instalador assistido do NM-Method"
  print_info "Raiz do projeto: $ROOT_DIR"

  architecture="$(detect_architecture)"
  print_info "Arquitetura do processador: $architecture"
  if is_arm64_architecture "$architecture"; then
    print_info "Modo ARM64: o instalador vai oferecer requirements-arm64.txt."
  fi

  python_bin="$(select_python)"
  require_command "$python_bin" "Python 3"

  if ask_yes_no "Deseja configurar o ambiente Python?" "y"; then
    install_python_environment "$python_bin" "$architecture"
  fi

  if ask_yes_no "Deseja configurar o ambiente Node/React?" "y"; then
    install_node_environment
  fi

  print_header "Concluido"
  print_info "Instalacao assistida finalizada."
}

main "$@"
