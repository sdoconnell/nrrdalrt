#/usr/bin/env bash
# bash completion for nrrdalrt

shopt -s progcomp
_nrrdalrt() {
    local cur prev firstword complete_options
    
    cur=$2
    prev=$3
	firstword=$(__get_firstword)

	GLOBAL_OPTIONS="\
        config\
        start\
        stop\
        version\
        --config\
        --help"

	case "${firstword}" in
	config)
		complete_options="--help"
		complete_options_wa=""
		;;
	start)
		complete_options="--help"
		complete_options_wa=""
		;;
	stop)
		complete_options="--help"
		complete_options_wa=""
		;;
	version)
		complete_options="--help"
		complete_options_wa=""
		;;

	*)
        complete_options="$GLOBAL_OPTIONS"
        complete_options_wa=""
		;;
	esac


    for opt in "${complete_options_wa}"; do
        [[ $opt == $prev ]] && return 1 
    done

    all_options="$complete_options $complete_options_wa"
    COMPREPLY=( $( compgen -W "$all_options" -- $cur ))
	return 0
}

__get_firstword() {
	local firstword i
 
	firstword=
	for ((i = 1; i < ${#COMP_WORDS[@]}; ++i)); do
		if [[ ${COMP_WORDS[i]} != -* ]]; then
			firstword=${COMP_WORDS[i]}
			break
		fi
	done
 
	echo $firstword
}
 
complete -F _nrrdalrt nrrdalrt
