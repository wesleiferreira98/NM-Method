#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
BACKEND_DIR="$ROOT_DIR/apps/backend"
FRONTEND_DIR="$ROOT_DIR/apps/frontend"
BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"
FRONTEND_URL="http://127.0.0.1:5173"

BACKEND_PID=""
FRONTEND_PID=""

print_header() {
  printf "\n==> %s\n" "$1"
}

print_info() {
  printf "    %s\n" "$1"
}

stop_services() {
  print_header "Encerrando servicos"

  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    print_info "Parando frontend PID $FRONTEND_PID"
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    print_info "Parando backend PID $BACKEND_PID"
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}

check_prerequisites() {
  print_header "Checando ambiente"

  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    printf "Ambiente virtual Python nao encontrado em %s.\n" "$VENV_DIR" >&2
    printf "Execute primeiro: ./install.sh\n" >&2
    exit 1
  fi

  if ! "$VENV_DIR/bin/python" -m uvicorn --version >/dev/null 2>&1; then
    printf "Uvicorn nao encontrado no ambiente virtual.\n" >&2
    printf "O pacote correto e 'uvicorn', nao 'unicorn'.\n" >&2
    printf "Execute: source .venv/bin/activate && pip install \"uvicorn[standard]\"\n" >&2
    printf "Ou execute novamente: ./install.sh\n" >&2
    exit 1
  fi

  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    printf "Dependencias do frontend nao encontradas em %s/node_modules.\n" "$FRONTEND_DIR" >&2
    printf "Execute primeiro: ./install.sh\n" >&2
    exit 1
  fi

  print_info "Ambiente Python encontrado em: $VENV_DIR"
  print_info "Dependencias Node encontradas em: $FRONTEND_DIR/node_modules"
}

start_backend() {
  print_header "Iniciando backend"
  (
    cd "$BACKEND_DIR"
    "$VENV_DIR/bin/python" -m uvicorn main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT"
  ) &
  BACKEND_PID="$!"
  print_info "Backend em: http://$BACKEND_HOST:$BACKEND_PORT"
}

start_frontend() {
  print_header "Iniciando frontend"
  (
    cd "$FRONTEND_DIR"
    npm run dev
  ) &
  FRONTEND_PID="$!"
  print_info "Frontend em: $FRONTEND_URL"
}

main() {
  trap stop_services EXIT INT TERM

  print_header "Inicializador do Ancestor-Based MCTS"
  check_prerequisites
  start_backend
  start_frontend

  print_header "Aplicacao em execucao"
  print_info "Abra: $FRONTEND_URL"
  print_info "Use Ctrl+C para encerrar backend e frontend."

  wait "$BACKEND_PID" "$FRONTEND_PID"
}

main "$@"
