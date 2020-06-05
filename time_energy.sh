#!/bin/bash

mytime=$(time ( /bin/bash energy_measure.sh ) 2>&1 )
#mytime=$(time ( /bin/bash energy_measure.sh ) 2>&1 1>/dev/null )
echo $mytime
