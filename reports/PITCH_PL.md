# FieldShift — pitch lokalny po polsku (3 min, te same 7 slajdów po angielsku)

Deck: https://www.figma.com/slides/BwBCfFOnQlypsikuAxev7I · Aplikacja: https://nowakdoma.github.io/NASA/

Slajdy są po angielsku (ta sama wersja co globalnie); mówimy po polsku. Jury lokalne może nie
znać rolnictwa w USA, więc slajdy 1–2 tłumaczą problem prostymi słowami, a slajd 4 zamienia
algorytmy w obrazy. Zasada: **nigdy „rolnik powinien posadzić X”**; mówimy „przy tych
priorytetach X wypada najlepiej w N na 10 przebiegów”. Nie dodawaj liczb spoza tego tekstu.

Około 400 słów, czyli spokojne 3 minuty. Zdania w [nawiasach] można pominąć, jeśli brakuje czasu.

---

## 1. Cover · 0:00–0:20

> Dzień dobry, jesteśmy [zespół]. To, co widzicie, to hrabstwo Finney w Kansas, z satelity.
> Te koła to pola: każde podlewa jedno ramię zraszacza, które obraca się wokół środka jak
> wskazówka zegara. Wodę pompuje się z ogromnego podziemnego zbiornika Ogallala. FieldShift
> pomaga rolnikowi zapytać: co dałby inny płodozmian na moim polu, kiedy wody jest coraz mniej?

## 2. The problem · 0:20–0:45

> Ubytek tej wody widać z kosmosu. Satelity NASA GRACE mierzą drobne zmiany grawitacji, a z
> nich ilość wody w regionie: spadek o ok. 0,86 cm rocznie, ok. 21 cm od 2002 roku. To sygnał
> regionalny, nie jedna studnia, i tak to pokazujemy. Więc każdy wybór, co siać, jest dziś też
> wyborem, ile wody zużyć.

## 3. What FieldShift does · 0:45–1:00

> Cztery kroki, bez konta: twoje pole, twoje priorytety (także ile wody możesz pompować),
> porównanie czterech płodozmianów i podsumowanie dla doradcy. Nie mówimy, co siać. Mówimy, jak
> często płodozmian wypada najlepiej przy twoich priorytetach.

## 4. How it works · 1:00–1:35

> Jak to liczymy? Dane NASA: pogoda z 31 lat, zieleń pól z MODIS, woda z GRACE, nachylenie z
> SRTM, plus mapy upraw i gleb USDA. Potem modele fizyczne, nie „czarna skrzynka” AI. Wodę
> liczymy jak saldo konta: deszcz i nawadnianie wpływają, parowanie i rośliny wydają; to
> standard FAO-56. Z wody wynika plon i dochód, erozja ze wzoru RUSLE, materia organiczna z
> indeksu glebowego. Na koniec niepewność: każdy płodozmian przechodzi przez 31 lat pogody, a
> 2000 losowań wokół priorytetów rolnika daje „najlepszy w N na 10 przebiegów”.

## 5. Field 30 · 1:35–1:55

> Prawdziwe pole przy rzece Arkansas. 18 lat upraw z map USDA, w tym dziewięć lat lucerny.
> MODIS pokazuje, że gołej ziemi było ok. 3 miesiące w roku w latach 2008–2012, a w 2021–2025
> poniżej miesiąca. [Goła ziemia oznacza erozję i utratę materii organicznej.]

## 6. The flip · 1:55–2:35

> Najważniejszy moment. Bez limitu wody lucerna z kukurydzą wypada najlepiej w ok. 5 na 10
> przebiegów. *(klik)* Rolnik mówi: mogę pompować tylko 14 cali, ok. 36 cm rocznie. Teraz sorgo,
> pszenica i żyto jako poplon wypadają najlepiej w ok. 8 na 10, bo lucerna z kukurydzą
> potrzebuje ok. 18 cali. Uczciwie pokazujemy koszt: w typowym roku ok. 12 400 dolarów zysku
> zamiast ok. 54 000. To jest rozmowa do przeprowadzenia z doradcą.

## 7. Close · 2:35–3:00

> Każda wartość ma przedział od słabego do dobrego roku, a każdy płodozmian listę „sprawdź
> lokalnie” i pole „czego nie wiemy”. Dalej: walidacja z rolnikami i K-State oraz kolejne
> hrabstwa nad Ogallalą. FieldShift wspiera decyzję rolnika, nigdy jej nie zastępuje.
> Dziękujemy, link jest na slajdzie.

---

## Ściąga na pytania jury (po polsku)

**Słowniczek (gdyby padło pytanie o podstawy)**
- **Pivot (center pivot)**: obrotowy zraszacz na kołach; stąd okrągłe pola widoczne z satelity.
- **Ogallala**: podziemny zbiornik pod 8 stanami USA; uzupełnia się bardzo wolno, więc
  pompowanie go wyczerpuje.
- **Płodozmian**: kolejność upraw na polu w kolejnych latach (np. lucerna 3 lata, potem kukurydza 2).
- **Poplon (cover crop)**: roślina siana między uprawami głównymi (u nas żyto), żeby gleba
  nie leżała goła.

**Algorytmy, szczegółowo**
- **Bilans wodny FAO-56** (`engine/water_balance.py`): dzienne parowanie wzorcowe ET0 metodą
  Penmana-Monteitha z danych NASA POWER (temperatura, wilgotność, wiatr, promieniowanie) ×
  współczynnik uprawy Kc. Jeden „kubełek” glebowy na pole (pojemność wodna z SSURGO). Pivot
  dolewa wodę, gdy gleba przeschnie, maks. ok. 5,4 mm dziennie, z opcjonalnym limitem rocznym.
- **Plon i dochód** (`engine/strategies.py`): plon spada z niedoborem wody według
  współczynnika Ky (FAO-33); dochód = plon × cena − koszty z budżetów K-State − pompowanie.
- **Erozja RUSLE** (`engine/erosion.py`): A = R·K·LS·C·P; R z opadów POWER, K z gleby
  SSURGO, LS z nachylenia SRTM, C z uprawy. Tylko erozja wodna.
- **Indeks SCI** (`engine/soil_index.py`): uproszczony wskaźnik NRCS: resztki pożniwne,
  zabiegi uprawowe, erozja. Wynik > 0 oznacza, że materia organiczna raczej rośnie. Progi są
  wstępne (oznaczone jako placeholder).
- **Obecny płodozmian** (`engine/rotation.py`): najkrótszy powtarzający się cykl w ostatnich
  8 latach map upraw USDA; 3 alternatywy z katalogu.
- **Przedziały**: każdy rok startowy 1995–2025 to jedna próbka cyklu → percentyle 10/50/90
  (słaby / typowy / dobry rok).
- **Ranking (MCDA)** (`engine/mcda.py`, `web/src/lib/ranking.ts`): wagi priorytetów losowane
  z rozkładu Dirichleta wokół ustawień suwaków, metryki losowane z przedziałów p10–p90; 2000
  losowań, a „N na 10” to odsetek losowań, w których dany płodozmian ma najwyższy wynik ważony.
  Liczone w przeglądarce w ułamku sekundy, więc wynik reaguje od razu na suwaki.

**Typowe pytania**
- **Dlaczego nie AI / uczenie maszynowe?** Jeden cykl uprawy na rok i 31 lat pogody to mała
  próba. Modele fizyczne mają sensowne granice i da się je wytłumaczyć rolnikowi.
- **Czy GRACE to woda w studni rolnika?** Nie, to cała woda w regionie ok. 300 km. Mówimy to
  wprost w aplikacji.
- **Dlaczego tylko 50 pól?** Pola z uprawami, których kosztów nie umiemy uczciwie policzyć
  (np. ziemniaki), pomijamy zamiast wymyślać liczby.
- **Czego nie wiemy?** Ceny i koszty są stałe (budżety K-State), nie odejmujemy dzierżawy ani
  kosztów pivota i studni, nie liczymy erozji wiatrowej, pogoda to siatka ok. 50 km, pole jest
  przybliżone idealnym kołem, część parametrów jest wstępna. Wszystko jest w polu
  „What we don't know”.
- **Czy to działa gdzie indziej?** Dane NASA są globalne; mapy upraw i gleb są dla całych USA.
  Aplikacja to pliki statyczne, więc zarząd wody albo doradca może ją hostować za darmo.
- **Czemu „N na 10”, a nie rekomendacja?** Bo wynik zależy od pogody i priorytetów. Pokazujemy,
  jak pewny jest wynik, a decyzja zostaje u rolnika.
