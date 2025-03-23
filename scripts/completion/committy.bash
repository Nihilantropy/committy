#!/usr/bin/env bash
# Bash completion script for committy

_committy_completion() {
    local cur prev opts formats models
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--version --dry-run --format --model --edit --config --init-config --verbose --no-confirm --with-scope --max-tokens --analyze --no-color"
    formats="conventional angular simple"
    models="gemma3:12b phi3:mini llama3:70b phi3:medium"

    # Handle specific options
    case "${prev}" in
        --format|-f)
            COMPREPLY=( $(compgen -W "${formats}" -- "${cur}") )
            return 0
            ;;
        --model|-m)
            COMPREPLY=( $(compgen -W "${models}" -- "${cur}") )
            return 0
            ;;
        --config|-c)
            COMPREPLY=( $(compgen -f -- "${cur}") )
            return 0
            ;;
        --max-tokens)
            # Suggest some common token limits
            COMPREPLY=( $(compgen -W "128 256 512 1024" -- "${cur}") )
            return 0
            ;;
        *)
            ;;
    esac

    # For --option format, suggest only if current word starts with -
    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
        return 0
    fi
}

complete -F _committy_completion committy