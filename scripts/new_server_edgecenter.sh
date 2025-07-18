#!/bin/bash

# Создание директории .ssh
mkdir -p ~/.ssh

# Добавление SSH ключа в authorized_keys
echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDhIkG9n82K5Kx42SChzUdEsQqsLnFDkzObnvJZt353sq3zgy6RyjFSnESK5sUEOAV4bPCw54xpCwujNm/bJ9lqzc/ZRnlm3ODiIVfGr4mQxkIRQ0x9mNPCh5l2DdvBtWIkDsslWMmnxdU2zqIWY2ds4Ri/C7e9mJE+3bqBIR1uEtiKi+puV9xy533w3t13duIa0zp8gKLBFQxaDLnjfFdIxj1ehLi0BeF7eNJPZA/Krf3RLN45y3eKZAswo80I6kvSxk1lEbH13FQD89U23XjrR10K13gKrIHdMu2Q7obIL2GphiaBXnSkyOnpEquioBFVctFuwwScW4ZoDtfk+ITnHzovrxqad4Q3/pfxQXReBgyY6xgvEnKErLqpDUYDCWCWU7xN1GqvhTu70uPkhNWt6GagIgotEij8c8+VLlfGgrnk80j36Xubc6wlo8GjwqjclyvlZbR9FL5QmvlIWZuvgezlgDekhLCfSqtXDHralAzo4RGlwoATyvZow5ATXsQlq5HrbllPWkcin9KFh6C999MQUBDLBqNomTAyhKbELxMvUiQ3a4QD4kGBkHAKDVkVCT0FXVyrtUyjfGzsN+lTdr591pwWXqpvMMPncrHTIfwyM/9GO1YkVzN8uCD9mKTYzf1UVnWUp0HTQMHyIVOaTEoYriImFeD6tQJb+CeVsQ== ansible@81.163.28.97 >> ~/.ssh/authorized_keys

# Настройка репозиториев и установка WireGuard
echo "deb http://archive.debian.org/debian buster-backports main non-free" >> /etc/apt/sources.list
apt-get update
apt-get install --no-install-recommends wireguard-tools 

# Установка pip и Docker
apt-get install -y python3-pip
pip3 install docker