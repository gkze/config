# vi: ft=zsh
# shellcheck shell=bash disable=SC2034,SC2296

# Zsh builtins help
&>/dev/null unalias run-help && autoload run-help

# Load completion system
zmodload zsh/complist
autoload -Uz +X compinit bashcompinit

# Tune the completion system a bit
zstyle ':completion:*' menu select
bindkey -M menuselect '^[[Z' reverse-menu-complete

# Keep elements of {,MAN}PATH{,S} unique
typeset -U PATHS MANPATHS PATH MANPATH

# Initialize Sheldon and load configured plugins
eval "$(sheldon source)"

# Add local Zsh functions path
# shellcheck disable=SC2206
fpath=( "${XDG_CONFIG_DATA:-"${HOME}.local/share"}/zsh/site-functions" $fpath )

# Set and export the Homebrew prefix here since it is needed below and during
# general shell use
export HOMEBREW_PREFIX="/opt/homebrew"

# Since a lot of the below configuration depends on Homebrew-installed
# software, let's activate it now. Taken from the output of "brew shellenv"
export \
  GOPATH="${HOME}/go" \
  HOMEBREW_CELLAR="${HOMEBREW_PREFIX}/Cellar" \
  HOMEBREW_REPOSITORY="${HOMEBREW_PREFIX}" \
  INFOPATH="${HOMEBREW_PREFIX}/share/info:${INFOPATH:-}" \
  MANPATH="${HOMEBREW_PREFIX}/share/man${MANPATH+:$MANPATH}:" \
  PATH="${HOMEBREW_PREFIX}/bin:${HOMEBREW_PREFIX}/sbin${PATH+:$PATH}" \
  PLAID_PATH="${HOME}/Development/github.plaid.com/plaid"

# Lazily configure Google Cloud SDK <=> Zsh integration in the background since
# it's slow
typeset -r GCLOUD_SDK_PATH="${HOMEBREW_PREFIX}/Caskroom/google-cloud-sdk/latest/google-cloud-sdk"
typeset -a GCLOUD_SDK_ZSH_FILES=( "path.zsh.inc" "completion.zsh.inc" )

# zsh-defer is loaded by Sheldon
for file in ${GCLOUD_SDK_ZSH_FILES[@]}; do
  zsh-defer source "${GCLOUD_SDK_PATH}/${file}"
done

# Aliases
alias \
  exap='exa -agilstype --color=always --icons' \
  exat='exa -gilstype --color=always --icons --tree' \
  kc=kubectl \
  nvc='cd "${HOME}/.config/nvim" && nvim init.lua' \
  pbc=pbcopy \
  pbp=pbpaste

# Activate direnv
source <(direnv hook zsh)

# Activate zoxide
eval "$(zoxide init zsh)"

# Activate Starship Zsh prompt
eval "$(starship init zsh)"

# Activate completion systems
compinit
bashcompinit

# Function to scan a directory tree for a desired directory name pattern and
# compile a "/.*PATH/"-style list, i.e. given ^bin$ /dir1/bin:/dir2/bin, etc
find_path_dirs() {
  local searchpath="${1}" pattern="${2}" maxdepth="${3}"

  fd -d"${maxdepth}" -td "${pattern}" "${searchpath}" | sd '/\n' ':' | sd ':$' ''
}

# Configure PATH via a readonly array which then gets joined on ":" by Zsh's
# array-joining syntax / flag - (j...)
# Docs on array splitting and joining in Zsh:
# https://zsh.sourceforge.io/Guide/zshguide05.html#l124
declare -a PATHS=(
  "${HOME}/.local/bin"
  "${PLAID_PATH}/go.git/bin"
  "${HOME}/.krew/bin"
  "${HOME}/go/bin"
  "${HOME}/.cargo/bin"
  "${HOMEBREW_PREFIX}/opt/openssl@3/bin"
  "$(find_path_dirs "${HOMEBREW_PREFIX}/lib/ruby/gems" "^bin$" 2)"
  "${HOMEBREW_PREFIX}/opt/ruby/bin"
  "${HOMEBREW_PREFIX}/opt/mysql-client/bin"
  "$(find_path_dirs "${HOMEBREW_PREFIX}/Cellar" "^gnubin$" 4)"
)

# Configure MANPATH in the same fashion as PATH
declare -a MANPATHS=( 
  "$(find_path_dirs "${HOMEBREW_PREFIX}/Cellar" "^man$" 4)"
  "$(find_path_dirs "${HOMEBREW_PREFIX}/Cellar" "^gnuman$" 4)"
)

# Single export for both by joining arrays above
export \
  PATH="${(j.:.)PATHS}:${PATH}" \
  MANPATH="${(j.:.)MANPATHS}:${MANPATH}"
