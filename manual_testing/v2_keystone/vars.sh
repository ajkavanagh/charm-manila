#/bin/bash

# Set up vars common to all the configuration scripts

export OVERCLOUD="./novarc"
export UNDERCLOUD="$HOME/novarc"

# Set serverstack defaults, if not already set.
[[ -z "$GATEWAY" ]] && export GATEWAY="10.5.0.1"
[[ -z "$CIDR_EXT" ]] && export CIDR_EXT="10.5.0.0/16"
[[ -z "$FIP_RANGE" ]] && export FIP_RANGE="10.5.150.0:10.5.200.254"
[[ -z "$NAMESERVER" ]] && export NAMESERVER="10.245.160.2"
[[ -z "$CIDR_PRIV" ]] && export CIDR_PRIV="192.168.21.0/24"
[[ -z "$SWIFT_IP" ]] && export SWIFT_IP="10.245.161.162"

# handy function to test if an array contains a value $1 in ${2[@]}
# returns $? as 1 if the element does exist
elementIn () {
  local e
  for e in "${@:2}"; do [[ "$e" == "$1" ]] && return 0; done
  return 1
}

