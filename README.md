# TerraFirmaGreg (TFG-Modern) Metal Calculator

Esse repositório tem como objetivo auxiliar os Jogadores do modpack de Minecraft ( 1.20.1) TFG a calcular a quantidade de insumos necessários para fazer o número de ingots desejado visando o menor execesso possível.

 ### Nota: 
   - Esse repositório está em desenvolvimento, e não há garantia de que ele abranja todos os metais e ligas possíveis.
   - Este repositório assume que você possui o conhecimento basico de como utilizar o mod Minescript para Forje e como adiciona-ló a sua instancia do modpack.
   - Os cálculos podem estar incorretos e não funcionarem corretamente com ligas mais complexas. *Use por sua conta e risco*.
   - Esse script é recomendado para o início do modpack, para o end-game provavelmente esse script ficará obsoleto


## Como Funciona
Após configurar o script na pasta correta ( recomendo o uso de um link simbolico para a pasta ). Ao entrar no seu mundo e precisar fazer X quantidades de ingots você irá abrir o chat e digitar '\alloy [metal_name] {quantity_of_ingots}'. Exemplo: \alloy bronze 12


O script irá buscar em seu inventário cada insumo necessário, baseado em um JSON pré configurado, com o nome do insumo e sua respectiva quantidade de metal ao ser derretido. Note que para que o menor excesso possivel o scrip pode sugerir que você faça mais lingotes que o desejado. *OBS: até a data que escrevo esse README não implementei um sistema para fazer menos ingots que a quantidade que o usuário especificou, se você não tem os materiais necessários para fazer a quantidade de metal desejada, vá minerar!*


## Metais e Ligas suportadas até o momento
 - Bronze | proporção 3:1
 
