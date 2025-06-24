#!/bin/bash

title()
{
green=`tput setaf 2`
reset=`tput sgr0`

echo ""
echo ""
echo "${green}**********************$1**********************${reset}"
echo ""
echo ""
sleep 1s 
}

info_flat()
{
green=`tput setaf 2`
reset=`tput sgr0`

echo "${green} $1 ${reset}"
sleep 1s 
}


info_enter()
{
green=`tput setaf 2`
reset=`tput sgr0`

echo ""
echo "${green} $1 ${reset}"
sleep 1s 
}


title  "DEPLOY PROJECT for Mqtt, Kafka and MongoDB"

info_enter "Create mqttkafka network"
docker network create mqttkafka

info_enter "Up docker compose with name 'iot-project' "
docker compose -p "iot-project" -f ./docker-compose.yml up -d 


echo  "!!!!! Deploy completed !!!!!"

sleep 1s

