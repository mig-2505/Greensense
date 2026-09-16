# GreenSense - Inteligência Artificial para Botânica e Agronegócio

O **GreenSense** é um sistema moderno de Visão Computacional que automatiza a detecção e medição (largura e altura) de plantas em tempo real. Evoluindo de técnicas clássicas de filtragem de cores (HSV) para o uso de Inteligência Artificial de ponta, o sistema é capaz de identificar plantas em ambientes complexos, ignorando ruídos e mudanças de iluminação.

## Funcionalidades Principais
*   **Detecção com IA (YOLOv8):** Utiliza um modelo treinado em um dataset customizado (via Roboflow e Google Colab) para focar 100% no espécime.
*   **Calibração Fixa Inteligente:** Converte medidas virtuais (pixels) em métricas reais (centímetros) através de um rápido processo de calibração manual por cliques.
*   **Dashboard Interativo:** Interface limpa e amigável desenvolvida em Streamlit, permitindo o monitoramento ao vivo.
*   **Registro e Histórico:** Captura de frames e armazenamento automático de métricas em CSV para análise de crescimento ao longo do tempo.

## Tecnologias Utilizadas
*   **Python:** Linguagem base do projeto.
*   **Ultralytics (YOLOv8):** Arquitetura de rede neural convolucional para detecção de objetos.
*   **OpenCV:** Processamento de imagens e renderização das *bounding boxes*.
*   **Streamlit:** Criação do Dashboard web (Frontend).
*   **Roboflow:** Anotação de imagens e criação do Dataset.

---

## Como Executar o Projeto

### 1. Clonar e Preparar o Ambiente
Primeiro, faça o clone deste repositório e instale as dependências:
```bash
git clone https://github.com/mig-2505/Greensense
cd Greensense
pip install opencv-python streamlit ultralytics numpy pandas
```

### 2. Inserir o Modelo de I.A.
Certifique-se de que o seu modelo treinado (`best.pt`) esteja localizado no diretório correto:

*   **Caminho exigido:** `visao_computacional/modelos/best.pt`

### 3. Realizar a Calibração Fixa
Antes de rodar o sistema pela primeira vez (ou caso mude a câmera de posição), posicione um objeto de tamanho conhecido (ex: folha A4 de 21cm) na cena e rode:

```bash
python visao_computacional/gerar_calibracao_fixa.py
```

> Siga as instruções no terminal para clicar nas extremidades do objeto. Isso gerará o arquivo `calibracao.json` automaticamente.

### 4. Iniciar o Dashboard
Com o sistema calibrado, inicie a interface de monitoramento:

```bash
streamlit run app/app.py
```
Acesse o sistema pelo seu navegador no endereço indicado (geralmente `http://localhost:8501`).

---

## Estrutura do Projeto
*   `app/`: Arquivos do painel web (Streamlit), contendo as páginas de monitoramento, histórico e mapa.
*   `dados/`: Pasta gerada automaticamente para armazenar as fotos capturadas e o arquivo `medidas_dashboard.csv`.
*   `visao_computacional/`: Núcleo da inteligência.
    *   `/core/`: Lógicas de medição, manipulação de arquivos (`io_utils.py`) e desenho na tela.
    *   `/modelos/`: Onde habita o cérebro do sistema (`best.pt`).
    *   `gerar_calibracao_fixa.py`: Script para setup da câmera.
