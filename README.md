# Koci Tinder - prosty Flask

Aplikacja pozwala:
- założyć konto,
- zalogować i wylogować użytkownika,
- usunąć konto razem z danymi,
- pobierać losowe zdjęcia kota z TheCatAPI,
- przesuwać kota w prawo/lewo,
- zapisywać historię decyzji w SQLite,
- korzystać z własnego API JSON aplikacji.

## Uruchomienie

```bash
cd koci_tinder
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Wejdź w przeglądarce na:

```text
http://127.0.0.1:5000
```

## Klucz TheCatAPI

Aplikacja zadziała bez klucza w prostym trybie, ale najlepiej dodać klucz API:

```bash
export CAT_API_KEY="twoj_klucz"
export SECRET_KEY="losowy_sekret"
python app.py
```

Na Windows PowerShell:

```powershell
$env:CAT_API_KEY="twoj_klucz"
$env:SECRET_KEY="losowy_sekret"
python app.py
```

## Własne API

### GET `/api/cat/random`
Zwraca losowego kota z TheCatAPI.

### POST `/api/swipes`
Zapisuje decyzję użytkownika.

Przykład JSON:

```json
{
  "cat_id": "abc123",
  "cat_url": "https://cdn2.thecatapi.com/images/abc123.jpg",
  "direction": "right"
}
```

`direction` może mieć wartość `right` albo `left`.

### GET `/api/swipes`
Zwraca historię decyzji zalogowanego użytkownika.

### DELETE `/api/account`
Usuwa konto zalogowanego użytkownika i jego dane.

## Struktura

```text
koci_tinder/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── swipe.html
│   ├── history.html
│   └── account.html
└── static/
    ├── style.css
    └── swipe.js
```
Apka wykonanana przez:
Aleksandra Rzemińska
Kamila Pęgiel
Michał Leśniak