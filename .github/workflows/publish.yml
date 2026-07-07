name: Publicar posts de Instagram

on:
  schedule:
    # Horarios en UTC (Argentina = UTC-3)
    - cron: "0 11 * * *"   # 08:00 ART -> desayuno
    - cron: "0 15 * * *"   # 12:00 ART -> almuerzo
    - cron: "0 18 * * *"   # 15:00 ART -> merienda
    - cron: "0 21 * * *"   # 18:00 ART -> cena
  workflow_dispatch:
    inputs:
      post_slot:
        description: "Franja horaria para probar manualmente"
        required: false
        type: choice
        options:
          - desayuno
          - almuerzo
          - merienda
          - cena
        default: desayuno

permissions:
  contents: write   # necesario para que el script pueda commitear/pushear temp_hosting

jobs:
  publicar:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout del repo
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Determinar franja horaria (POST_SLOT)
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "POST_SLOT=${{ inputs.post_slot }}" >> "$GITHUB_ENV"
          else
            case "${{ github.event.schedule }}" in
              "0 11 * * *") echo "POST_SLOT=desayuno" >> "$GITHUB_ENV" ;;
              "0 15 * * *") echo "POST_SLOT=almuerzo" >> "$GITHUB_ENV" ;;
              "0 18 * * *") echo "POST_SLOT=merienda" >> "$GITHUB_ENV" ;;
              "0 21 * * *") echo "POST_SLOT=cena" >> "$GITHUB_ENV" ;;
              *) echo "POST_SLOT=" >> "$GITHUB_ENV" ;;
            esac
          fi

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Instalar dependencias
        run: pip install -r requirements.txt

      - name: Ejecutar bot
        env:
          POST_SLOT: ${{ env.POST_SLOT }}
          GOOGLE_OAUTH_CLIENT_ID: ${{ secrets.GOOGLE_OAUTH_CLIENT_ID }}
          GOOGLE_OAUTH_CLIENT_SECRET: ${{ secrets.GOOGLE_OAUTH_CLIENT_SECRET }}
          GOOGLE_OAUTH_REFRESH_TOKEN: ${{ secrets.GOOGLE_OAUTH_REFRESH_TOKEN }}
          GDRIVE_FOLDER_ORIGINALES: ${{ secrets.GDRIVE_FOLDER_ORIGINALES }}
          GDRIVE_FOLDER_EDITADAS: ${{ secrets.GDRIVE_FOLDER_EDITADAS }}
          GDRIVE_FOLDER_APROBADAS: ${{ secrets.GDRIVE_FOLDER_APROBADAS }}
          GDRIVE_FOLDER_PUBLICADAS: ${{ secrets.GDRIVE_FOLDER_PUBLICADAS }}
          IG_USER_ID: ${{ secrets.IG_USER_ID }}
          IG_ACCESS_TOKEN: ${{ secrets.IG_ACCESS_TOKEN }}
        run: python main.py
