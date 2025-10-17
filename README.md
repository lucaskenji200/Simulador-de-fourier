# 🎼 Simulador Interativo de Séries de Fourier

Este projeto é uma aplicação de desktop interativa, desenvolvida em Python, que permite visualizar a aproximação de funções definidas por partes através de suas Séries de Fourier. A interface gráfica foi construída com **Tkinter** e os gráficos são gerados dinamicamente com **Matplotlib**.

O simulador permite ao usuário:
-   Definir até 5 funções diferentes em intervalos distintos.
-   Ajustar o número de termos ($n$) da série de Fourier em tempo real com um controle deslizante.
-   Visualizar a animação da aproximação da série conforme o número de termos é alterado.
-   Salvar a animação completa (de $n=1$ a 100) como um arquivo **GIF animado**.


## ✨ Funcionalidades Principais

-   **Interface Gráfica Intuitiva**: Fácil de usar, com campos de entrada claros para as funções e seus intervalos.
-   **Múltiplas Funções**: Combine diferentes expressões matemáticas (ex: `x**2`, `sin(x)`, `10`) em intervalos consecutivos para criar funções complexas por partes.
-   **Visualização em Tempo Real**: O gráfico da série de Fourier é atualizado instantaneamente ao mover o controle deslizante do número de termos, com uma animação suave entre os estados.
-   **Cálculo Simbólico**: Utiliza a biblioteca **SymPy** para calcular as integrais dos coeficientes $a_0$, $a_n$ e $b_n$ de forma precisa.
-   **Exportação para GIF**: Com um único clique, gere e salve uma animação da aproximação da série, variando $n$ de 1 a 100, ideal para apresentações e compartilhamento.

---

## 🛠️ Tecnologias Utilizadas

-   **Python 3**: Linguagem principal do projeto.
-   **Tkinter**: Para a construção da interface gráfica (GUI).
-   **Matplotlib**: Para a plotagem dos gráficos da função original e da série.
-   **SymPy**: Para realizar os cálculos matemáticos simbólicos necessários (integração).
-   **NumPy**: Para a manipulação eficiente de arrays numéricos para a plotagem.
-   **Pillow (PIL)**: Para processar os quadros da animação e criar o arquivo GIF final.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

Certifique-se de ter o **Python 3** instalado em sua máquina.

### 1. Salve o Código
Salve o código fornecido em um arquivo, por exemplo, `fourier_simulator.py`.

### 2. Crie um Ambiente Virtual (Recomendado)

Abra o terminal na pasta onde você salvou o arquivo e execute:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

Com o ambiente virtual ativado, instale todas as bibliotecas necessárias com um único comando:

```bash
pip install sympy numpy matplotlib Pillow
```

### 4. Execute o Simulador

Agora, execute o script:

```bash
python fourier_simulator.py
```

---

## 📦 Como Compilar para um Executável (App)

É possível empacotar a aplicação em um único arquivo executável (`.exe` para Windows), que pode ser executado em outros computadores sem a necessidade de instalar o Python ou qualquer biblioteca.

### 1. Instale o PyInstaller

```bash
pip install pyinstaller
```

### 2. Execute o Comando de Compilação

Navegue até a pasta do projeto pelo terminal e execute o seguinte comando:

```bash
pyinstaller --onefile --windowed --name="SimuladorFourier" fourier_simulator.py
```
-   `--onefile`: Cria um único arquivo executável.
-   `--windowed`: Impede que um console de terminal seja aberto ao executar a aplicação.

O executável final estará na pasta `dist/` que será criada no diretório do projeto.
