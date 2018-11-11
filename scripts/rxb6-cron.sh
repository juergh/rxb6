#!/bin/bash
#
# Script to use as a cronjob
#
# Copyright (C) 2018 Juerg Haefliger <juergh@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)

function doit()
{
	# Load the module
	if ! grep -q "^rxb6 " /proc/modules ; then
		sudo insmod "${DIR}"/../rxb6.ko
		sleep 1
		sudo chmod 666 /dev/rxb6
		sudo raspi-gpio set 6 pn
	fi

	# Collect the data
	"${DIR}"/rxb6-log.py "${DIR}"/rxb6.config "${DIR}"/rxb6.db
}

doit 2>&1 >> "${DIR}"/rxb6.log
