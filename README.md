# LASERbeamer

Vesmírná arkádová hra v Pythonu a Pygame. Ovládej loď, nabíjej laser,
uhýbej pilám, střelám a kyselině a přežij všech **10 vln**. V páté a desáté
vlně přichází boss. Po vyčištění vlny získáš 12 bodů štítu, nejvýše do 100.

## Spuštění

Vyžaduje Python **3.10+** a grafické prostředí. Z kořene repozitáře:

```sh
python -m venv .venv
```

Aktivace prostředí na Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Na Linuxu/macOS:

```sh
source .venv/bin/activate
```

Potom:

```sh
python -m pip install -r requirements.txt
python game.py
```

Jediná externí závislost je Pygame 2.6.1. Shapely ani screeninfo nejsou potřeba.
Cesty ke grafice se odvozují od zdrojového souboru, takže lze hru spustit
i z jiného pracovního adresáře. Složka `assets` musí zůstat vedle `game.py`.

## Ovládání

| Klávesa | Akce |
| --- | --- |
| W / šipka nahoru | Dopředný tah |
| A, D / šipky vlevo, vpravo | Otáčení |
| S / šipka dolů | Brzda |
| Shift / B | Boost, obnovuje se po 2,5 s |
| Krátce podržet a pustit mezerník | Červený laser |
| Držet mezerník 1 s | Silnější modrý laser, vystřelí automaticky |
| Esc | Pauza / pokračování / zavření podnabídky |
| F11 | Celá obrazovka |
| F3 | Diagnostika FPS, počtů objektů a kolizních kružnic |
| Šipky / W, S + Enter | Nabídky; funguje také myš a numerický Enter |

Laser míří ve směru lodi, krátce ji následuje a každého nepřítele zasáhne
nejvýše jednou za výstřel. Červený způsobí 2 body poškození, nabitý 7.
Po zásahu má hráč 0,65 s ochrany. Barevné body na okraji označují nepřátele
mimo obrazovku. Ztráta zaměření okna automaticky pozastaví hru.

## Nepřátelé

| Typ | Chování | Zbraň | Skóre |
| --- | --- | --- | --- |
| Sawer | Pronásleduje hráče | Saw — letící pila | 100 |
| Sniper | Udržuje odstup | Bullets — rychlá střela | 150 |
| Acider | Útočí ze střední vzdálenosti | Acid — trojice pomalých projektilů | 200 |
| Boss | Střídá salvy a kruhové útoky | Střely a pily | 1 500 |

Sniper se může objevit od druhé vlny a Acider od třetí. Boss má 65 životů
v páté a 100 v desáté vlně. Zničení všech nepřátel desáté vlny znamená vítězství.

## Struktura podle přiloženého schématu

- `game.py`: bezpečný vstupní bod; import nespouští herní smyčku.
- `laserbeamer/model.py`: `Object → CollisionAble → Player / Enemy / Projectile`;
  `Menu` dědí z `Object`. `Enemy` má potomky `Sawer`, `Sniper`, `Acider`, `Boss`;
  `Projectile` má `Saw`, `Bullets`, `Acid`, `PlayerLaser`.
- `laserbeamer/app.py`: načítání původní grafiky, vykreslování, ovládání,
  nabídky, změna velikosti okna a ukládání rekordu.
- `tests/test_game.py`: regresní testy herních pravidel i obsluhy obrazovek.
- `assets/`: původní obrázky a font. Noví nepřátelé mají odlišné barevné
  geometrické siluety kreslené Pygame. Původní `polygons.json` zůstává zachován
  jako podklad; nová logika používá kružnice a průnik úsečky s kružnicí.

Simulace běží pevným krokem 120 Hz nezávisle na obnovování obrazu. Dlouhý
zásek je omezen na 0,25 s simulace na snímek. Projektily mají omezenou životnost,
částice omezený počet a zásahy rychlých střel se vyhodnocují podél celé dráhy
jednoho kroku. Pauza zastavuje všechny herní časovače a ruší rozpracované nabíjení.

Hra ukládá pouze nejlepší skóre při konci hry, restartu nebo ukončení:

- Windows: `%APPDATA%/LASERbeamer/score.json`
- macOS: `~/Library/Application Support/LASERbeamer/score.json`
- Linux: `$XDG_DATA_HOME/LASERbeamer/score.json`, případně `~/.local/share/LASERbeamer/score.json`

Poškozený soubor se ignoruje. Chyba zápisu nezpůsobí pád; nabídka zobrazí upozornění.
Rozehranou kampaň nelze uložit a po zavření okna začíná nová hra.

## Ověření

```sh
python -m unittest discover -s tests -v
python game.py --smoke-test
```

Testy používají SDL dummy driver, neotevírají skutečné okno a nemění hráčův rekord.
Smoke test vykreslí deset herních snímků včetně existujících obrázků a skončí.
GitHub Actions spouští stejné kontroly na Linuxu s Pythonem 3.10 a 3.12.

Automatické testy kontrolují pohyb při 30/60/144 FPS, laser a nabíjení,
průběžné kolize, životnost projektilů, skóre, ochranu po zásahu, smrt,
vlny a vítězství, pauzu, restart, nabídky, přepočet myši při změně velikosti
okna a ukládání rekordu. Nenahrazují ruční posouzení obtížnosti kampaně
ani kontrolu skutečného fullscreen režimu na jednotlivých operačních systémech.
