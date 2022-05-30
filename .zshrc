# Vi mode
set -o vi

# Enable Ctrl+R reverse history search
bindkey -v
bindkey '^R' history-incremental-search-backward

# Builtins help
unalias run-help && autoload run-help

# Add custom completion functions path
fpath=(~/.local/zsh/site-functions "${fpath[@]}")

# Tune completion system a bit
# Use Tab to select completion option
zstyle ':completion:*' menu select
zstyle ':completion:*' accept-exact '*(N)'
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path ~/.cache/zsh

# completion initialization function
autoload -Uz compinit && compinit -I

HOMEBREW_EXE="/opt/homebrew/bin/brew"
HOMEBREW_PREFIX="$(${HOMEBREW_EXE} --prefix)"

# Homebrew shell environment
eval "$(${HOMEBREW_EXE} shellenv)"

# Zsh plugins via Sheldon
eval "$(sheldon source)"

# Starship Zsh prompt
eval "$(starship init zsh)"

# zoxide ("z", smart "cd")
eval "$(zoxide init zsh)"

# direnv (auto-source .envrc files)
eval "$(direnv hook zsh)"

# kubectl Zsh completion
source <(kubectl completion zsh)

# ASDF - instal multiple versions of CLI tools & languages
source "${HOMEBREW_PREFIX}/opt/asdf/libexec/asdf.sh"

# Alias for luamake to where it was built
alias luamake="${HOME}/Development/github.com/sumneko/lua-language-server/3rd/luamake/luamake"

# Alias pbcopy & pbpaste to pbc & pbp for speed
alias pbc=pbcopy pbp=pbpaste

# nvc == NeoVim Config. `cd`s into ~/.config/nvim and opens it up
alias nvc='cd ~/.config/nvim && nvim init.lua'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #  
#                  === executable / $PATH-related settings ===                  #
# Environment variables are normally defined in ~/.zshenv, but since ~/.zshrc   #
# is sourced _after_ ~/.zshenv, and we want to have exact control over the      #
# ordering of $PATH, we define what we would like to expose first in that order #
# at the bottom of ~/.zshrc, since this is the last section to get sourced      #
# before the shell becomes available for use.                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #  

# Set default editor
export EDITOR="nvim"

# Set man pager to bat for coloring
export MANPAGER="sh -c 'col -bx | bat -l man -p'"

# Fixes git failing to sign commits
export GPG_TTY="$(tty)"

# FZF - fuzzy search
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Go executables
export GOPATH="${HOME}/go"
export PATH="${GOPATH}/bin:${PATH}"

# Keg-only Ruby executables
export PATH="${HOMEBREW_PREFIX}/opt/ruby/bin:${PATH}"

# System-wide Homebrew Ruby executables
export PATH="${HOMEBREW_PREFIX}/lib/ruby/gems/3.0.0/bin:${PATH}"

# User-local Gem executables
export PATH="${HOME}/.local/share/gem/ruby/3.0.0/bin:${PATH}"

# Keg-only MySQL client
export PATH="${HOMEBREW_PREFIX}/opt/mysql-client/bin:${PATH}"

# Keg-only OpenSSL
export PATH="${HOMEBREW_PREFIX}/opt/openssl@3/bin:${PATH}"

# Relied on by Plaid tooling
export PLAID_PATH="${HOME}/Development/github.plaid.com/plaid"

# Cargo (Rust dependency, build, package & release multitool)
source "$HOME/.cargo/env"

# User-local executables
export PATH="${HOME}/.local/bin:${PATH}"

# Plaid Go Monorepo executables
export PATH="${PLAID_PATH}/go.git/bin:${PATH}"

# Formula-bundled man pages
export MANPATH="$(fd -td ^man$ ${HOMEBREW_PREFIX}/Cellar | tr '\n' ':' | sed 's/:$//g'):${MANPATH}"

# GNU binaries and man pages
export MANPATH="$(fd -td ^gnuman$ ${HOMEBREW_PREFIX}/Cellar | tr '\n' ':' | sed 's/:$//g'):${MANPATH}"

# Expose non-"g"-prefixed GNU executables (i.e. "tar" instead of "gtar" etc.)
export PATH="$(fd -td ^gnubin$ ${HOMEBREW_PREFIX}/Cellar | tr '\n' ':' | sed 's/:$//g'):${PATH}"

# Broot
source "${HOME}/.config/broot/launcher/bash/br"
