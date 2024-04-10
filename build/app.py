from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import os
import datetime
import random
import mysql.connector
import time



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Chave secreta para flash messages

def gerar_cabecalho_edi(numero_pedido, tipo_pedido, data_pedido, data_entrega, codigo_comprador):
    numero_pedido = str(numero_pedido).zfill(15)
    tipo_pedido = str(tipo_pedido).zfill(3)
    data_pedido = data_pedido.strftime("%Y%m%d")
    data_entrega = data_entrega.strftime("%Y%m%d")
    codigo_comprador = str(codigo_comprador).zfill(13)
    fornecedor = "0000000000000"  
    codigo_local = "0000000000000"  
    cabecalho = f"01{numero_pedido}{tipo_pedido}{data_pedido}{data_entrega}{data_entrega}{codigo_comprador}{fornecedor}{codigo_local}\n"
    return cabecalho

def converter_planilha_para_texto(df, numero_pedido, tipo_pedido, data_pedido, data_entrega,numero_pedido_atual):
    try:
        # Loop pelas colunas representando cada pedido
        for coluna_pedido in df.columns[2:]:
            try:
                # Identificar o código do comprador do pedido
                codigo_comprador = str(coluna_pedido).zfill(13)  # Código do comprador é o próprio cabeçalho da coluna

                # Gerar o cabeçalho EDI para o pedido atual
                cabecalho_edi = gerar_cabecalho_edi(numero_pedido, tipo_pedido, data_pedido, data_entrega, codigo_comprador)

                print("Cabeçalho EDI gerado:", cabecalho_edi)  # Verificar o cabeçalho EDI gerado

                # Inicializar o texto com o cabeçalho
                texto = cabecalho_edi

                # Loop pelas linhas do pedido, começando da segunda linha (índice 1) para pular o cabeçalho
                for index, row in df.iterrows():
                    # Extrair código, descrição e quantidades da linha atual
                    codigo_produto = str(row[df.columns[0]]).zfill(12)
                    descricao_produto = str(row[df.columns[1]]).ljust(34)
                    quantidade = "{:07.0f}".format(row[coluna_pedido] * 1000).replace(",", "")

                    # Construir a linha do arquivo de texto de acordo com o modelo
                    linha = f"03{numero_pedido}{tipo_pedido}{codigo_produto}000001{descricao_produto}{quantidade}\n"

                    # Adicionar a linha ao texto final
                    texto += linha

                print("Texto final:", texto)  # Verificar o texto final antes de gravar no arquivo

                # Obter o diretório padrão para salvar o arquivo .txt
                tmp_dir = 'tmp'

# Verifica se o diretório existe e, se não, cria
                if not os.path.exists(tmp_dir):
                    os.makedirs(tmp_dir)

                # Obtém o caminho completo do arquivo na pasta "tmp"
                save_path = os.path.join(tmp_dir, f"EDI_{numero_pedido_atual}.txt")

                # Salvar o texto em um arquivo .txt
                with open(save_path, "w") as file:
                    file.write(texto)

                # Exibir mensagem de sucesso com o caminho do arquivo
                print(f"A conversão do pedido {coluna_pedido} foi concluída com sucesso. O arquivo foi salvo em: {save_path}")
            except Exception as e:
                print(f"Ocorreu um erro ao processar o pedido {coluna_pedido}: {str(e)}")
    except Exception as e:
        print(f"Ocorreu um erro ao processar a planilha: {str(e)}")





def converter_planilha_EDI(df, numero_pedido, tipo_pedido, data_pedido, data_entrega, ean_dia):
    
    
    try:
        ean_dia = str(ean_dia)  
      
        # Gerar o cabeçalho EDI
        cabecalho_edi = gerar_cabecalho_edi(numero_pedido, tipo_pedido, data_pedido, data_entrega, ean_dia)

        # Inicializar o texto com o cabeçalho
        texto = cabecalho_edi

        # Verificar se os dados estão sendo processados corretamente
        for index, row in df.iterrows():  # Agora iterando sobre todas as linhas
            
            

            # Extrair código, descrição e quantidades da linha atual
            tipo_produto = "000"
            codigo_produto = str(row[df.columns[0]]).zfill(12)
            print('codigoprotudo:',codigo_produto)
            unidade_embalagem = "000001"
            descricao_produto = str(row[df.columns[1]])[:34].ljust(34)
            print('descricao',descricao_produto)
            quantidades = "".join("{:07.0f}".format(cell * 1000).replace(",", "") for cell in row[df.columns[2:]])
            print('quantidade',quantidades)

            # Construir a linha do arquivo de texto de acordo com o modelo
            linha = f"03{numero_pedido.zfill(15)}{tipo_produto}{codigo_produto}{unidade_embalagem}{descricao_produto}{quantidades}\n"

            # Adicionar a linha ao texto final
            texto += linha
        save_dir = os.path.dirname(__file__)
        save_path = os.path.join(save_dir, "edi_brasil.txt")

        # Salvar o texto em um arquivo .txt
        with open(save_path, "w") as file:
            file.write(texto)

      
        flash(f"A conversão foi concluída com sucesso. O arquivo foi salvo em: {save_path}", 'success')
    except Exception as e:
        flash(f"Ocorreu um erro: {str(e)}", 'error')


@app.route('/diabrasil',methods=['GET', 'POST'])
def diabrasil():
    tipos_pedido = {
    "Pedido Normal": "001",
    "Carga Extra": "002",
    "Atecipado I - Dia %": "003",
    "Atecipado II - Dia %": "004",
    "NÃO UTILIZAR - Antigo Gru": "005",
    "Prévia higienizados": "006",
    "Gerar OP Processados": "007",
    "Previsão de colheita": "008",
    "Atecipado - FHO": "009",
    "Atecipado - Funcionários": "010",
    "Frango Assado": "011",
    "Atecipado - Chia I Box": "012",
    "WalMart": "013",
    "Rede Oba": "014",
    "Teste": "015",
    "Pedido Frubana": "016",
    "OC Aumento": "017"
}
    ean_dia={"DIA BRASIL ANHANGUERA" : "7000000000045",
                   "DIA BRASIL GUARULHOS"  : "7000000000046",
                   "DIA BRASIL MAUA - 712" : "7899288907117"}

    df = None  # Define df as None initially
    if request.method == 'POST':
        file = request.files['file']
        if file.filename != '':
            df = pd.read_excel(file)
            converter_planilha_EDI(df)
            return redirect(url_for('diabrasil'))  # Redirecio
    
    
    return render_template('diabrasil.html', df=df,tipos_pedido=tipos_pedido,ean_dia=ean_dia)



def gerarNumeroPedidoAutomatico():
    
    edicaisp='EDICAISP'
    
    # Gera uma parte numérica aleatória de 5 dígitos
    parte_numerica = str(random.randint(1, 99999)).zfill(5)
    
    return   edicaisp+parte_numerica

 
@app.route('/converter', methods=['POST'])
def converter():
    try:
        # Variável para rastrear o número do pedido atual
        numero_pedido_atual = None

        # Verifica se o número do pedido está presente no formulário
        if 'numero_pedido' in request.form:
            numero_pedido_atual = request.form['numero_pedido'].strip()

        # Verifica se o número do pedido está vazio ou se é None
        if not numero_pedido_atual:
            # Gera o número de pedido automaticamente
            numero_pedido_atual = gerarNumeroPedidoAutomatico()
            
        print('Numeropedidoautomatico:',numero_pedido_atual)
        tipo_pedido = request.form['tipo_pedido']
        data_pedido = datetime.datetime.strptime(request.form['data_pedido'], "%Y-%m-%d")
        data_entrega = datetime.datetime.strptime(request.form['data_entrega'], "%Y-%m-%d")

        df = pd.read_excel(request.files['file'])

        # Início da função converter_planilha_para_texto
        try:
            # Inicializar o texto com o cabeçalho
            texto = ""

            # Loop pelas colunas representando cada pedido
            for coluna_pedido in df.columns[2:]:
                try:
                    print("Iterando coluna:", coluna_pedido)

                    # Verifica se o cabeçalho é diferente do anterior
                    if df[coluna_pedido].name != numero_pedido_atual:
                        # Se for diferente, incrementa o número do pedido
                        numero_pedido_atual = incrementarNumeroPedido(numero_pedido_atual)

                    # Gerar o cabeçalho EDI para o pedido atual
                    cabecalho_edi = gerar_cabecalho_edi(numero_pedido_atual, tipo_pedido, data_pedido, data_entrega, coluna_pedido)

                    # Adicionar o cabeçalho ao texto final
                    texto += cabecalho_edi

                    # Loop pelas linhas do pedido, começando da segunda linha (índice 1) para pular o cabeçalho
                    for index, row in df.iterrows():
                        # Extrair código, descrição e quantidades da linha atual
                        codigo_produto = str(row[df.columns[0]]).zfill(12)
                        descricao_produto = str(row[df.columns[1]])[:34].ljust(34)

                        quantidade = "{:07.0f}".format(row[coluna_pedido] * 1000).replace(",", "")

                        # Construir a linha do arquivo de texto de acordo com o modelo
                        linha = f"03{numero_pedido_atual}{tipo_pedido}{codigo_produto}000001{descricao_produto}{quantidade}\n"

                        # Adicionar a linha ao texto final
                        texto += linha

                    print("Pedidos adicionados ao texto com sucesso para o pedido:", coluna_pedido)
                except Exception as e:
                    print(f"Ocorreu um erro ao processar o pedido {coluna_pedido}: {str(e)}")

            # Obter o diretório padrão para salvar o arquivo .txt
            tmp_dir = 'tmp'

# Verifica se o diretório existe e, se não, cria
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)

            # Obtém o caminho completo do arquivo na pasta "tmp"
            save_path = os.path.join(tmp_dir, f"EDI_{numero_pedido_atual}.txt")

            print("Caminho do arquivo:", save_path)

            # Salvar o texto em um único arquivo .txt
            with open(save_path, "w") as file:
                file.write(texto)

            print("Arquivo gerado com sucesso.")

            return send_file(save_path, as_attachment=True)
        except Exception as e:
            print(f"Ocorreu um erro ao processar a planilha: {str(e)}")
            return "Ocorreu um erro ao processar a planilha."
        # Fim da função converter_planilha_para_texto

    except Exception as e:
        flash(f"Ocorreu um erro: {str(e)}", 'error')
        return redirect(url_for('index'))
    
    

def incrementarNumeroPedido(numero_pedido):
    # Extrair o número final do pedido
    numero_final = numero_pedido[9:]

    # Converter para inteiro e incrementar
    numero_incrementado = int(numero_final) + 1

    # Formatar o número incrementado com zero à esquerda para garantir 15 caracteres
    numero_incrementado_formatado = str(numero_incrementado).zfill(6)

    # Concatenar com o prefixo e retornar
    return f"{numero_pedido[:9]}{numero_incrementado_formatado.zfill(6)}"




def limpar_pasta_tmp():
    pasta_tmp = 'tmp'
    try:
        # Verifica se a pasta existe
        if os.path.exists(pasta_tmp):
            # Lista todos os arquivos na pasta
            arquivos = os.listdir(pasta_tmp)
            for arquivo in arquivos:
                caminho_completo = os.path.join(pasta_tmp, arquivo)
                # Remove cada arquivo na pasta
                os.remove(caminho_completo)
            print("Conteúdo da pasta 'tmp' foi removido com sucesso.")
        else:
            print("A pasta 'tmp' não existe.")
    except Exception as e:
        print(f"Erro ao limpar a pasta 'tmp': {e}")

 
@app.route('/', methods=['GET', 'POST'])
def index():
    tipos_pedido = {
    "Pedido Normal": "001",
    "Carga Extra": "002",
    "Atecipado I - Dia %": "003",
    "Atecipado II - Dia %": "004",
    "NÃO UTILIZAR - Antigo Gru": "005",
    "Prévia higienizados": "006",
    "Gerar OP Processados": "007",
    "Previsão de colheita": "008",
    "Atecipado - FHO": "009",
    "Atecipado - Funcionários": "010",
    "Frango Assado": "011",
    "Atecipado - Chia I Box": "012",
    "WalMart": "013",
    "Rede Oba": "014",
    "Teste": "015",
    "Pedido Frubana": "016",
    "OC Aumento": "017"
}

    df = None  # Define df as None initially
    if request.method == 'POST':
        file = request.files['file']
        if file.filename != '':
            df = pd.read_excel(file)
            converter_planilha_para_texto(df)
            return redirect(url_for('index'))  # Redireciona para a página inicial para mostrar a planilha
    return render_template('index.html', df=df,tipos_pedido=tipos_pedido)





if __name__ == '__main__':
    
    app.run(host='0.0.0.0',debug=True,port=3333)
