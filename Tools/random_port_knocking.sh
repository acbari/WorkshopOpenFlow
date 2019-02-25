#!/bin/bash

#Urutan yang benar: 2000, 3000, 4000, 5000

# Wrong sequence:
echo -n "*" | nc -q1 -u 10.0.0.2 2000
echo -n "*" | nc -q1 -u 10.0.0.2 4000
echo -n "*" | nc -q1 -u 10.0.0.2 3000
