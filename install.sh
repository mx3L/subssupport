#!/bin/bash

D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
E2_USERNAME="root"

usage (){
    echo "usage: HOST [USERNAME PASSWORD]"
    return
} 

if [ -n "$1" ];
then
	E2_HOST=$1
fi

if [ -n "$2" ];
then
	E2_USERNAME=$2
fi
if [ -n "$3" ];
then
	E2_PASSWORD=$3
fi

if [ -z $E2_HOST ]; then
    usage
    exit 1
fi

with_pass=
if [ $# -eq 5 ]; then
    with_pass=1
fi
    
echo "connection parameters: $E2_HOST $E2_USERNAME $E2_PASSWORD"
echo "creating ipk..."
${D}/create_ipk.sh > /dev/null
IPK_NAME=$(ls -vt ${D}|grep '\.ipk'|head -n 1)
echo $IPK_NAME

echo "uploading '${IPK_NAME}' to $E2_HOST..."
if [ -f "$with_pass" ]; then
	ftp -n $E2_HOST <<- EOFFTP > /dev/null
		user $E2_USERNAME $E2_PASSWORD
		binary
		cd /tmp
		lcd ${D}
		put $IPK_NAME
		bye
	EOFFTP
else
    scp $IPK_NAME $E2_USERNAME@$E2_HOST:/tmp
fi
   
echo "installing '${IPK_NAME}' to $E2_HOST..."
if [ -f "$with_pass" ]; then
	sshpass -p $E2_PASSWORD ssh $E2_USERNAME@$E2_HOST <<- EOFSSH > /dev/null
		opkg remove enigma2-plugin-extensions-subssupport
		opkg --force-downgrade install /tmp/$IPK_NAME
		rm /tmp/$IPK_NAME
	EOFSSH
else
	ssh $E2_USERNAME@$E2_HOST <<- EOFSSH > /dev/null
		opkg remove enigma2-plugin-extensions-subssupport
		opkg --force-downgrade install /tmp/$IPK_NAME
		rm /tmp/$IPK_NAME
	EOFSSH
fi
