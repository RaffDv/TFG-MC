# TerraFirmaGreg (TFG-Modern) Metal Calculator

Esse repositório tem como objetivo auxiliar os Jogadores do modpack de Minecraft ( 1.20.1) TFG a calcular a quantidade de insumos necessários para fazer o número de ingots desejado visando o menor execesso possível.

 ### Nota: 
   - Esse repositório está em desenvolvimento, e não há garantia de que ele abranja todos os metais e ligas possíveis.
   - Este repositório assume que você possui o conhecimento basico de como utilizar o mod Minescript para Forje e como adiciona-ló a sua instancia do modpack.
   - Os cálculos podem estar incorretos e não funcionarem corretamente com ligas mais complexas. *Use por sua conta e risco*.
   - Esse script é recomendado para o início do modpack, para o end-game provavelmente esse script ficará obsoleto


## Como Funciona
Após configurar o script na pasta correta ( recomendo o uso de um link simbolico para a pasta ). Ao entrar no seu mundo e precisar fazer X quantidades de ingots você irá abrir o chat e digitar '\alloy [metal_name] {quantity_of_ingots}'. Exemplo: \alloy bronze 12


O script irá buscar em seu inventário cada insumo necessário, baseado em um JSON pré configurado, com o nome do insumo e sua respectiva quantidade de metal ao ser derretido. Note que para que o menor excesso possivel o scrip pode sugerir que você faça mais lingotes que o desejado. 
***OBS: até a data que escrevo esse README não implementei um sistema para fazer menos ingots que a quantidade que o usuário especificou, se você não tem os materiais necessários para fazer a quantidade de metal desejada, vá minerar!***


## Metais e Ligas suportadas até o momento
 - Bronze
 - Black Bronze
 - Bismuth Bronze
 - iron ( olhe a nota abaixo )
 - tin
 - copper

### Nota:
   - Como a receita do iron usa 1 charcoal para cada 1 lingote e utiliza o mesmo calculo dos outros metais e ligas, pode haver sobras que provavelmente serão perdidas ou a Bloomery não irá aceitar
   - Tenha em mente que o script só calcula a quantidade de dusts de Iron e não a quantidade de charcoal, embora a quantidade de charcoal será a quantidade de ligotes que o script calculará
   - Para ter certeza que não haverá erros, **aconselho** que jogue 4 dusts junto de 4 charcoal e repita esse processo até o fim dos dusts
   - Também ,obviamente, **aconselho** que use uma quantidade que seja multipla de 4

 
