#!/bin/sh

source="$HOME/projects/linkding"

target="$1"
if [ -z "$target" ] ; then
	echo "Bitte ein Ziel als Argument angeben."
	exit 1
fi

excludes="$source/deploy_excludes"
if [ ! -f "$excludes" ] ; then
	echo "Datei nicht gefunden: $excludes"
	exit 1
fi

includes="$source/deploy_includes"
if [ ! -f "$includes" ] ; then
	echo "Datei nicht gefunden: $includes"
	exit 1
fi

target_path="projects/linkding"
target_port="22"
# Wenn "true", dann machen wir vor dem tatsächlichen Rsync-Aufruf einen
# Trockendurchlauf.
dry_run="false"

case $target in
	"alphaville")
		target_host="alphaville.jeziorny.dev"
		target_user="worker"
		dry_run="true"
		;;
	*)
		target_host=""
		target_user=""
esac

if [ -z "$target_host" ] || [ -z "$target_user" ] ; then
    echo "Unbekanntes Ziel: $target"
    exit 1
fi

echo "Ziel: $target_user@$target_host"

if [ "$dry_run" = "true" ] ; then
    echo
    echo "Trockendurchlauf: "
    rsync --dry-run -e "ssh -p $target_port" --recursive --progress \
		--delete-after \
		--include-from="$includes" \
		--exclude-from="$excludes" \
		"$source"/ "$target_user"@"$target_host":$target_path/
    echo
    echo -n "Das war der Trockendurchlauf. Weiter?"
    read -r inp
    if [ "$inp" != "y" ] && [ "$inp" != "j" ] && [ "$inp" != "ja" ] && [ "$inp" != "yes" ] ; then
        echo 'abbrechen…'
        exit 0
    fi
fi

rsync -e "ssh -p $target_port" --recursive --progress \
	--delete-after \
	--include-from="$includes" \
	--exclude-from="$excludes" \
	"$source"/ "$target_user"@"$target_host":"$target_path"/
echo "$target OK."

# vim: tw=0:wrap
