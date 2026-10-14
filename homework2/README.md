# 4-битный сумматор на транзисторах 2N7000

Сумматор с последовательным переносом (ripple-carry) из 77 дискретных
полевых транзисторов, без единой микросхемы. Складывает два 4-битных числа
и входной перенос: A + B + Cin, результат от 0 до 31 горит на пяти светодиодах.

**[Схема в симуляторе Falstad](https://www.falstad.com/circuit/circuitjs.html?ctz=CQAgjCAMB0l3BWcMBMcUHYMGZIA4UA2ATmIxAUgoqoQFMBaMMAWACgAPcQkFAFnBge-EALSiGgRhBAHCCAhEEC8IIGkQQJwgAHQDOgQRBAwiCAeEF2AGEFmA+EEACIBs0bA-CDHNgbhBArCCAWEGOAmECMO7gGRAlu6w9MHeVtjP3V5Aw0AOQBZAHkAZQ0UKIx4DQAKQAwQBkBcEEBUEA1VAEdkjVlTA3lAdhBpTRNKooAHDTBIDUAuEEA8EF0ASnYuIQoUQR4EEYEwAUBKEEBFEDsO+TkHa2N-QI67QDkQQHEQD22ALg1qg11F7Vki0vUwaA1AAhAHau1vWSMjrVcHEydpYydFBoAMIAewArgAXDQJbDQlDQsDQ9rqVxLZ53dSAdBBPLMlGp1FZTG5-lcNAgNIAkEAANBYAipSepkRToOwAEogYg8MAoPAgQiTHlQIV8WhCqgwBDsADuHK5gqEVG5vMg0u4isFmBGSqgqs14EF2DwAuVqsNxtEnP1JrYMr4lu1hAQcutMsdzpAGEIvO1KptHq9VpAeDw6pdQZDgdIWsFvplUcDzHGgd96jVCcIiuII0VIAAZgBDAA26jo7DQ5AV4Cz4E9VYmIAAgth2AAnNNgauVlBOoVteDsADmae7XIzvAw2Z1bFTeu1s+rOYLxdLbHL4611Z53urAgbKFb67rh5HvfgvqHepPl4nYvYqbNgYfHcnECXJbLkHIT53cCPu9YbBtt+IwPieipnoOICgT2oE3uKd4Wu6dpcgu4B5kW76rp+iFHgg3J-o2vptshf6WmByD9mwQ4kSeNFwVOqZuoGTHPr26HLh+5AsdWhA3qxAgAELNoBfI9qxTHkX2cCQRJPYSfRKb+t6gqetuL7sZha6qUeGBGgRAn7iJ2msdpkkQVRSm8D2pkKQhwahuGmbqW+K5rvZR54PaO4gAJAFtu5rHuWZlFDkFPZBbZ04cp2grxqxi4Ya52FxZ2cBqaIPlEdFG4jPGwXSRZeU9nlkWpom0bemASbxWhLmcYI1WdkI6UCECACWAB2B7lUePX5eeDUjCefWRYMfACNgYC8vwE1TRlQyAOQgdR2Gs6gNgMfIilBc0YFtk28pMPBLfYq0CRtzDYDw+36pd20HdwICAPggARBLY51XfyoxQZ9h0gPcBjVKYgDyIE4GiQB8DbIqoLTqAJUMw+1HVFOogBJhMjCSQDS6hAgB7KWiKVA-b+4qiKKJMSqq+O-mAtYE1OMo0zwdPYEmdOxlBrO-uMB3E6q3Ok1QaQCGzqpCwLjni+z7l020PYi36stM9TKDYBMvMKyrauKiKPPwQrOvi1Veny22jOG7Tn3gZRubgONogRmbfARlQKDQBAqDsDbUwCHhWq1r7Qqu+70CGUOZv8+Hdt62u3v2w5TtULuvox3bAfagHgnJ9hjuffxP0gFEYAAPq+oMeBM9gYjl6IlfzQIhcHizWscxMlsUQVNuq4nEZN3Hgdu1AIee1B4gB73AcuwPHsWePBpJggUdTmuXd97gwsRkn9Ur2PkA+-h9fF1nX6s59l0HfnUQoCXG2XRMtd8IQd-C7bBeGW2-N0x-bdSb6NskQnwwDrO14FPIebA-6WgDvzCeIDg6h0AQg6Bi8j44QAWgjemV6okQzhGDOBdD71S-j7O2D9n5RGwNfTgFBDQ1wEIQGhfB74v3IQeMWdM2Hf3MjbXiEwIxsOAUHQehluE3gDmLGBgjp5DnESpXeFBkH1R4X3JiaDX6ULXEogOTE8HkPUdhDhAgJyJwvnwShXAMBTFoUGSxjDn6WKiHwEoDZACpRGdES0tfzS04dbIMTs+7SwEaA4RvjeQB3chIoJkFwmCnCQorC5AjRAKoHgVWfd66mJQYkig+EUkjDwYjeqXiBCeSZhfBAZigzEETrXUg1S7H10lCJRWhtIBy28R3ZAIgAHNIAZPOBw82giDTq0sY+E+lCMgs0iOIz5ECGjtnSAXSHZpTSQXDJ9VBl7y1CsnR5SUE9Nzp+VuZDCAVLaIQCukwhCXLrgXQg3VNaG0eaQ08PjuS-m6c8wJ-TwH6i5vhbkqSIk-LDo8iOYK4kxzQN3RUU116JxAAU+JfzaAArhdk+sUQ9kbOebnfg58yEYDOfwJ+4BK6ksmPXDA3UDYy1pe03+ZLaYO1pd8iZvywDYH9gCg2wL2Vh15fKXlkLs5cqZg7S6MKMpRFOfssVGKyVjh0US-Z9LKVdPzhjc6fA5q2PAHhA6TD7F4BKAkbqCBjbUwtcLBlAyECswdtavu4zp5e3tXkgFTq+VSP1XpCOXqRUVndX3Kqt1VGFz0UG+enrbq7Mjb6m1h0Pn5xxudBAxBha1yEBmqxlKC7EBKKCSE70+TiGYDwR+CKhj-UBiDVoENETqGhhoXyzRgSNo0GjJt6gEhgCxkCQyeMK1yToT2EmW0kDk2gI0uMw6uS1iYuzM2TFe6LtNEmbRgo11+n5kxMW26ZT7vChGA9EsWIzNPc0lijzL03rEgbS9D6xJOu3abBdYlaxGNeR02OOB508D-f3H5Xs7bGU-QGF1YCw6fr0mbEM5MNmgdutqQD-5EOGIDChgMgkAIx0-WW6sX6D5FwAmXCtVTeDVxIFWg+jcN0wSTF+q2HSV6Ad7oByDwTWMBnYxB2B-KW4ej0r3eDt5kWsdumvD0YbGy4ewtx3kUntLEbk8fEYX6z4enEPXK+pHvojGo6IR+fIKN5svgeXdPZ+ZMfboykigHrO3U48PezAZrN8ckVBhBukfYxOJkvbC9mw18Jk75LBlplN8Ow-gkjhCVKj1A9pguFC9MIBoYZ+hvJDNmeEm2I9AG5E2Z-sPJRgGxYcf466vkN5tLlY85Eiy5W9Ji1E-MriNXbp7pk5fWLyLSsBj3dF3RqmPSFfEF+ojazevmMsYZvAs3TPMMccUFxbj-InuPYLcQzHGVZMA+5Crnngl7YDAd+rIKJY+Ylq1gLCS-H7dSahqbI2Tu8lyZZVqL2+HiBKVphFWLpuVMJhR2pJmaMF0aabC9YkZlFa4Z0wxyHYdOcq2Ar2iyMPelh+dgTzSrvNJu-sjH0muQrKew43rMdifGTJ0N8pI28dlqOX96Vpy9PnPI7Ci5YPbkyoeak69j3tu2YGdCknN11Mo6O6L38xlHnaWcxZQF6nYOPMJzi2XyH0VPdTci95gtMPa7p5T7O8uy34pZ1SwH3I+AGYo5y23POzPUqaU+rkBs4dvPlYBqY+BxeK69t7zDHucc+t97yfHBt1d6+98hyV4v65s42UH708flMFyJQzj3ZbbeGKS727Vc1DNVSL4t41przV6RYk6z3P7g0+5r1LhrbrGOYZr6HrzRtDGwaddHmO9fkNpYA914uDP69t9uungHY-mtlozFthFA6005uLyQOhZf64FuKEWiEJa8C1nLUGWmD0a3A1BuoFAEN4RNphgZNt2Nr+dvRigftwkh0cnwp9YgYzhRkzFNOymHgb-P2IAsZVUM2YAwTSA9mXuSA-maAvmWKfCMWBAv0FAnJCMVAmUdySA5pLA5AYqAFR5fA5XD-LUA2Egigz1PSVAt9UAkAjkWsHbAZO2OKWseMAPW2SYYnM2TZIDXHA-XeRUQQsdW7Lg7KSMbyPcdDBHBMYnQSQyPDIAg-asMgJmGLQyMjDkB+SjIAnQszPyKA-CWApgkXX5FeeMWA1CaXcwpnEQXuPgxXIcBwoQwTZpNrEeKgSwuReMXcRQ+TOwiaORPg4jfwtTRgj6XkNQ6VK+TQ-TbQ0pXKfQ5hN+BBOA2KUw4rX5EieMeA6w5vHCPg6ZEQJwhBNoCdeUGZDwnIncTA7yAycLUnJZcCLpDQuLKI-2Vg4-XROItLKInQzLBI3nXLUbAQSAlAzI+HJReMFA-I4DarbZEQMWRw1HeBZY1w9Y0QlBaYniYqbyHrMIhY2Q89Vono+qCYgDcQaI9JIuOIixMYnQ+bB49Q+xZbVbA8HAjArwyYnxLJeMHAuY9lG2LJPggKYnUosEraMErYwpPxf41JXwqbQ4kE4nd7EIxFZEzA2sX7a4iHW4jaTyLwnQ0HDNF4hpbqGZXAykn4n9YnOKSkwEqrPg5kmZFYmwsOVk1w5pdwsQvg+kv3REinQ4lkkQPsLHU48pYU6k0nG8XEmVfEqhDnIY8tPQsku5fnXKIghEmkxlfXCQ0gjg1YmXFogUVJNkhrUFM0rkx5Hk-ZMXOKdFREpfPXMXZk9FdEgHYU4gg-C3OUolOIm3JIrkclIY53GlAUnlAUnUgZeVOKCgxktHJlJoylP3c0i7cPZALaDM205PdgzsePQU05YU+VZk+PD0-0xDKM93EQXEhIAMnVforkA1UM5hE1YoM1JpJ1XArs6MjlYNOKLshM4JKqaqHgp1NM3HccrkqcmEvXfszsIfCQ0IjZYNZkxcj0yUlcmgg-efCIjKIEYSQYdNZ47gHNUk3nLfHfEtC6LUIYG8+aHgU-OtdQbACGWEG-Ftd85tbGL81GdGbAftcEXfNgd-ctLLK5PjROP-cUAAv0e0ZqGsLkBCpdA-BChw5C9dW8tzeUDCndHCgMZY3Cw9YIhCgKIiiWMCggpCiDcA1khC0gyipdG0+ig2Ri8A1i+i8c3Cug0Yb0H01JZgjlO2G3PiuUPxTg2OJUYQ50EmdkxC-Ue0A-SaScVVAUPxbUESjKJsGQqShMHkBFISDZfinKCXaVYuQ88Aaud5IaKytAesexQw9CnjaqR5QSzuc3PxBwi3TgleXSrytlH1Lyy0Bw5SsTZeDyxTYIi3XcYScK0MKgKTXS4jWK+TFy1JTTUgnTIuCy2+P5VuaMRZXnVIiOBC8FASswiBMS0JeUbyo07I+0fSsoxq0o8FSBeUUK6ohqvxT5bqnyFK8gEiJKh2Rq5K9o0yheU0zFChCyvovKvkGhay4Y1hEigiqK8qrIkRaMe7KK8Suqzaq0QWKKgKrzZYlACLYIjqsQpRTS69Xqnrfqo43S69DBXRB606oXdUVJG4iy+4uap4uaszN41xD4h2Ui4a9a+HEEi3AKWqmw4E9SxqmG46+BGGy0AKS6zJBGvxNE6KqbB6qGiMHGjBA8wpcGkYX7TKvEiywkua0HRaszSHKi3ipm0gty2QzS7k2Ggo5kxqzm5GyZVks60nMSDGjZHgi3MU-UO60xB6nm5ZVMkaqmsWsSG05nSm+UiypUxalUgG5he5JpZizDG01yiqlFKW5SM0rm+YvU3Shi5quqy06MBqs00Wl05WdS903Gkmt2+KwQVXF68pWW42y2hGr6jPbK86ElOah3Aq+yqlcMyqYPBWiGr3H09S1iq2oEpMg622BW-mpXDO+0Vi12mOEsiWss3GjW3MmSxVX2q3WWjOs03PUygQGEQvZSQqkvDuuOguNsjs02LitvVXFOuvFy9S8czOpk1c3mie-OsOCe+0ccku7Oae8e5DSu8ylclyx1degOiOuc4erUXcymq8xU486OtfXW+xS8oC68w0ROslYMB8kALIeQX4DoAwQAMRBpAgZMhNAvgfg-hz9ABmEDMDkAZDAH6BAvkqmFFOEubvHWgsHhnRgebuGgQd1HvS6Wpgwb9DpSGXgZKL5kIboSftgbmVVC9G9GbrRNwbbHQZEHQafsTjSHYCECGnvSfuGmDRGAABM6ACwwRCwIQGBCw6BeG2IYLIAAIbYUBRSnRppn0O9Di5HJgFHeBUz1HWpb6LJuG9Jhpdy9YuB+BFR+QEqsyzGMpxBT7iIcHsHtZmHRBWG2B2HDYnZdZ9Ukw+GBH8whGRGxGJGcwpGZHvpvQtGrVlGt429nKtQtGQA26LIZYnUZZDGpwuAnxLGnZDotoxAqAEn34SHZlbZHG+BnHXGJrinQlhKeGQB+HBHhHRHxHJHB5pHh4051GKmqpInkV2nsNF7os6zIJOmA0k0EMqEI5LHH5vRMmNH4nUiqHbYRAFmpgSmynjNln3G+QyGam6nfGGmAnmmYBWnflq8BttnumNElHwLFQ4mC8LJlmX0yHUnS5HrLGsAj6cnZm7n-Im6RBaHVnfRXH-m3szSdmfG-HGnAm0Jgnh5RMumQXYmLnsI4X1H8dbmBo0Te8zTnmCS7zLHv9RxPnxAtU2AgA)**: открывается в браузере,
по переключателям можно щёлкать.

---

## Результаты работы

Фото устройства: **[папка Results](Results/)**

![Устройство](Results/device.jpg)

Пять плат: четыре платы разряда (по одной на бит) и плата ввода-вывода с
переключателями и светодиодами. Питание 5 В от модуля MB102.

### Как читать

- Рычажки DIP-8 слева направо: B0 B1 B2 B3 A0 A1 A2 A3. Рычажок вверх (к ON) = 1.
- Отдельный красный DIP-1 слева = Cin.
- Светодиоды слева направо: Cout S3 S2 S1 S0, веса 16 8 4 2 1.

### Тесты

Разбор трёх тестов: какой рычажок за что отвечает и какие светодиоды горят.

<p>
<img src="Results/test2_explained.jpg" width="32%"> <img src="Results/test9_explained.jpg" width="32%"> <img src="Results/test10_explained.jpg" width="32%">
</p>

| № | A | B | Cin | сумма | светодиоды Cout S3 S2 S1 S0 | фото |
|---|---|---|---|---|---|---|
| 1 | 0000 (0) | 0010 (2) | 0 | 2 | 0 0010 | [test1](Results/test1.jpg) |
| 2 | 0001 (1) | 0001 (1) | 0 | 2 | 0 0010 | [test2](Results/test2.jpg), [крупно](Results/test2_close.jpg) |
| 3 | 1000 (8) | 0010 (2) | 0 | 10 | 0 1010 | [test3](Results/test3.jpg) |
| 4 | 0100 (4) | 0110 (6) | 0 | 10 | 0 1010 | [test4](Results/test4.jpg) |
| 5 | 1000 (8) | 1010 (10) | 0 | 18 | 1 0010 | [test5](Results/test5.jpg) |
| 6 | 1100 (12) | 1110 (14) | 0 | 26 | 1 1010 | [test6](Results/test6.jpg) |
| 7 | 1100 (12) | 1111 (15) | 0 | 27 | 1 1011 | [test7](Results/test7.jpg) |
| 8 | 1100 (12) | 1110 (14) | 1 | 27 | 1 1011 | [test8](Results/test8.jpg) |
| 9 | 0001 (1) | 0001 (1) | 1 | 3 | 0 0011 | [test9](Results/test9.jpg) |
| 10 | 1111 (15) | 1111 (15) | 1 | 31 | 1 1111 | [test10](Results/test10.jpg) |

- 1 + 1 = 2: в младшем разряде 1 + 1, сумма 0 и перенос в следующий разряд.
- 4 + 6 = 10: перенос из разряда 2 в разряд 3.
- 8 + 10 = 18: в старшем разряде 1 + 1, перенос уходит наружу и загорается Cout.
- Тесты 7 и 8 дают 27 двумя способами: единица в младшем разряде пришла
  от B0 или от входного переноса Cin.
- 1 + 1 + 1 = 3: в младшем разряде складываются все три входа, сумма 1 и перенос 1.
- 15 + 15 + 1 = 31: максимум, перенос проходит через все 4 разряда, горят все 5 светодиодов.

Фото каждого теста отдельно (нажмите, чтобы открыть в полном размере):

<table>
<tr>
<td align="center"><b>Тест 1:</b> 0 + 2 = 2<br><a href="Results/test1.jpg"><img src="Results/test1.jpg" width="420"></a></td>
<td align="center"><b>Тест 2:</b> 1 + 1 = 2<br><a href="Results/test2.jpg"><img src="Results/test2.jpg" width="420"></a></td>
</tr>
<tr>
<td align="center"><b>Тест 3:</b> 8 + 2 = 10<br><a href="Results/test3.jpg"><img src="Results/test3.jpg" width="420"></a></td>
<td align="center"><b>Тест 4:</b> 4 + 6 = 10<br><a href="Results/test4.jpg"><img src="Results/test4.jpg" width="420"></a></td>
</tr>
<tr>
<td align="center"><b>Тест 5:</b> 8 + 10 = 18<br><a href="Results/test5.jpg"><img src="Results/test5.jpg" width="420"></a></td>
<td align="center"><b>Тест 6:</b> 12 + 14 = 26<br><a href="Results/test6.jpg"><img src="Results/test6.jpg" width="420"></a></td>
</tr>
<tr>
<td align="center"><b>Тест 7:</b> 12 + 15 = 27<br><a href="Results/test7.jpg"><img src="Results/test7.jpg" width="420"></a></td>
<td align="center"><b>Тест 8:</b> 12 + 14 + 1 = 27<br><a href="Results/test8.jpg"><img src="Results/test8.jpg" width="420"></a></td>
</tr>
<tr>
<td align="center"><b>Тест 9:</b> 1 + 1 + 1 = 3<br><a href="Results/test9.jpg"><img src="Results/test9.jpg" width="420"></a></td>
<td align="center"><b>Тест 10:</b> 15 + 15 + 1 = 31<br><a href="Results/test10.jpg"><img src="Results/test10.jpg" width="420"></a></td>
</tr>
</table>

---

## Сборка и пайка

Все пять плат с компонентами, до соединения кабелями:

![Платы сверху](Results/assembly/boards_top.jpg)

Плата ввода-вывода: сверху на этапе монтажа и снизу, готовая разводка.

<p>
<img src="Results/assembly/io_board_top.jpg" height="420"> <img src="Results/assembly/io_board_bottom.jpg" height="420">
</p>

Плата разряда снизу: шина +5 В сверху, шина GND снизу, между ними перемычки
между ячейками и провода к разъёму.

![Плата разряда снизу](Results/assembly/bit_board_bottom.jpg)

Низ плат разряда и система в сборе, соединённая кабелями:

<p>
<img src="Results/assembly/boards_bottom.jpg" width="40%"> <img src="Results/assembly/system_wired.jpg" width="57%">
</p>

---

## Как это работает

- **Вентиль И-НЕ**: два n-МОП транзистора последовательно и резистор 10 кОм к +5 В.
  Выход 0, только когда оба входа 1.
- **Полный сумматор** (один разряд): 9 вентилей И-НЕ, это 18 транзисторов и 9 резисторов.
  Складывает A, B, Cin и выдаёт сумму S и перенос Cout.
- **Перенос**: Cout разряда i идёт на Cin разряда i+1, как «1 в уме» при сложении
  столбиком. Перенос бежит от младшего разряда к старшему.

```
N1 = И-НЕ(A, B)      N4 = И-НЕ(N2, N3)  = A xor B
N2 = И-НЕ(A, N1)     N5 = И-НЕ(N4, Cin)
N3 = И-НЕ(B, N1)     N6 = И-НЕ(N4, N5)
                     N7 = И-НЕ(Cin, N5)
S    = И-НЕ(N6, N7)  = A xor B xor Cin
Cout = И-НЕ(N1, N5)  = A·B + Cin·(A xor B)
```

---

## Схемы

### Плата ввода-вывода и вся система

Рычажки через резисторы 10 кОм подают 0 или 5 В на входы, выходы разрядов
открывают транзисторы Q1–Q5, а те зажигают светодиоды. Четыре кабеля по
7 проводов идут к платам разряда.

![Плата ввода-вывода](Results/io_board_and_system.png)

### Плата разряда

Девять ячеек И-НЕ, разъём J1: +5V, GND, A, B, Cin, S, Cout.

![Плата разряда](Results/bit_board.png)

Остальные чертежи (расположение деталей по отверстиям, пайка снизу, цоколёвка):
[schematics/](schematics/), подробно в [assembly.md](assembly.md).

---

## Состав

| деталь | всего |
|---|---|
| транзистор 2N7000 | 77 (18 × 4 разряда + 5 на светодиоды) |
| резистор 10 кОм | 45 |
| резистор 470 Ом | 5 |
| светодиод 5 мм | 5 |
| DIP-переключатель на 8 и на 1 позицию | 1 + 1 |
| макетная плата 7×9 см | 5 |
| модуль питания MB102 | 1 |

```
Results/        фото устройства и основные схемы
schematics/     все чертежи (SVG)
sim/            схема для Falstad: ссылка и текст для импорта
tools/          генераторы чертежей и проверка раскладки на 512 комбинациях
assembly.md     сборка, проверка по шагам, таблица истинности разряда
wiring.md       список монтажа по отверстиям
```

---

## Как повторить

1. Открыть [схему в Falstad](https://www.falstad.com/circuit/circuitjs.html?ctz=CQAgjCAMB0l3BWcMBMcUHYMGZIA4UA2ATmIxAUgoqoQFMBaMMAWACgAPcQkFAFnBge-EALSiGgRhBAHCCAhEEC8IIGkQQJwgAHQDOgQRBAwiCAeEF2AGEFmA+EEACIBs0bA-CDHNgbhBArCCAWEGOAmECMO7gGRAlu6w9MHeVtjP3V5Aw0AOQBZAHkAZQ0UKIx4DQAKQAwQBkBcEEBUEA1VAEdkjVlTA3lAdhBpTRNKooAHDTBIDUAuEEA8EF0ASnYuIQoUQR4EEYEwAUBKEEBFEDsO+TkHa2N-QI67QDkQQHEQD22ALg1qg11F7Vki0vUwaA1AAhAHau1vWSMjrVcHEydpYydFBoAMIAewArgAXDQJbDQlDQsDQ9rqVxLZ53dSAdBBPLMlGp1FZTG5-lcNAgNIAkEAANBYAipSepkRToOwAEogYg8MAoPAgQiTHlQIV8WhCqgwBDsADuHK5gqEVG5vMg0u4isFmBGSqgqs14EF2DwAuVqsNxtEnP1JrYMr4lu1hAQcutMsdzpAGEIvO1KptHq9VpAeDw6pdQZDgdIWsFvplUcDzHGgd96jVCcIiuII0VIAAZgBDAA26jo7DQ5AV4Cz4E9VYmIAAgth2AAnNNgauVlBOoVteDsADmae7XIzvAw2Z1bFTeu1s+rOYLxdLbHL4611Z53urAgbKFb67rh5HvfgvqHepPl4nYvYqbNgYfHcnECXJbLkHIT53cCPu9YbBtt+IwPieipnoOICgT2oE3uKd4Wu6dpcgu4B5kW76rp+iFHgg3J-o2vptshf6WmByD9mwQ4kSeNFwVOqZuoGTHPr26HLh+5AsdWhA3qxAgAELNoBfI9qxTHkX2cCQRJPYSfRKb+t6gqetuL7sZha6qUeGBGgRAn7iJ2msdpkkQVRSm8D2pkKQhwahuGmbqW+K5rvZR54PaO4gAJAFtu5rHuWZlFDkFPZBbZ04cp2grxqxi4Ya52FxZ2cBqaIPlEdFG4jPGwXSRZeU9nlkWpom0bemASbxWhLmcYI1WdkI6UCECACWAB2B7lUePX5eeDUjCefWRYMfACNgYC8vwE1TRlQyAOQgdR2Gs6gNgMfIilBc0YFtk28pMPBLfYq0CRtzDYDw+36pd20HdwICAPggARBLY51XfyoxQZ9h0gPcBjVKYgDyIE4GiQB8DbIqoLTqAJUMw+1HVFOogBJhMjCSQDS6hAgB7KWiKVA-b+4qiKKJMSqq+O-mAtYE1OMo0zwdPYEmdOxlBrO-uMB3E6q3Ok1QaQCGzqpCwLjni+z7l020PYi36stM9TKDYBMvMKyrauKiKPPwQrOvi1Veny22jOG7Tn3gZRubgONogRmbfARlQKDQBAqDsDbUwCHhWq1r7Qqu+70CGUOZv8+Hdt62u3v2w5TtULuvox3bAfagHgnJ9hjuffxP0gFEYAAPq+oMeBM9gYjl6IlfzQIhcHizWscxMlsUQVNuq4nEZN3Hgdu1AIee1B4gB73AcuwPHsWePBpJggUdTmuXd97gwsRkn9Ur2PkA+-h9fF1nX6s59l0HfnUQoCXG2XRMtd8IQd-C7bBeGW2-N0x-bdSb6NskQnwwDrO14FPIebA-6WgDvzCeIDg6h0AQg6Bi8j44QAWgjemV6okQzhGDOBdD71S-j7O2D9n5RGwNfTgFBDQ1wEIQGhfB74v3IQeMWdM2Hf3MjbXiEwIxsOAUHQehluE3gDmLGBgjp5DnESpXeFBkH1R4X3JiaDX6ULXEogOTE8HkPUdhDhAgJyJwvnwShXAMBTFoUGSxjDn6WKiHwEoDZACpRGdES0tfzS04dbIMTs+7SwEaA4RvjeQB3chIoJkFwmCnCQorC5AjRAKoHgVWfd66mJQYkig+EUkjDwYjeqXiBCeSZhfBAZigzEETrXUg1S7H10lCJRWhtIBy28R3ZAIgAHNIAZPOBw82giDTq0sY+E+lCMgs0iOIz5ECGjtnSAXSHZpTSQXDJ9VBl7y1CsnR5SUE9Nzp+VuZDCAVLaIQCukwhCXLrgXQg3VNaG0eaQ08PjuS-m6c8wJ-TwH6i5vhbkqSIk-LDo8iOYK4kxzQN3RUU116JxAAU+JfzaAArhdk+sUQ9kbOebnfg58yEYDOfwJ+4BK6ksmPXDA3UDYy1pe03+ZLaYO1pd8iZvywDYH9gCg2wL2Vh15fKXlkLs5cqZg7S6MKMpRFOfssVGKyVjh0US-Z9LKVdPzhjc6fA5q2PAHhA6TD7F4BKAkbqCBjbUwtcLBlAyECswdtavu4zp5e3tXkgFTq+VSP1XpCOXqRUVndX3Kqt1VGFz0UG+enrbq7Mjb6m1h0Pn5xxudBAxBha1yEBmqxlKC7EBKKCSE70+TiGYDwR+CKhj-UBiDVoENETqGhhoXyzRgSNo0GjJt6gEhgCxkCQyeMK1yToT2EmW0kDk2gI0uMw6uS1iYuzM2TFe6LtNEmbRgo11+n5kxMW26ZT7vChGA9EsWIzNPc0lijzL03rEgbS9D6xJOu3abBdYlaxGNeR02OOB508D-f3H5Xs7bGU-QGF1YCw6fr0mbEM5MNmgdutqQD-5EOGIDChgMgkAIx0-WW6sX6D5FwAmXCtVTeDVxIFWg+jcN0wSTF+q2HSV6Ad7oByDwTWMBnYxB2B-KW4ej0r3eDt5kWsdumvD0YbGy4ewtx3kUntLEbk8fEYX6z4enEPXK+pHvojGo6IR+fIKN5svgeXdPZ+ZMfboykigHrO3U48PezAZrN8ckVBhBukfYxOJkvbC9mw18Jk75LBlplN8Ow-gkjhCVKj1A9pguFC9MIBoYZ+hvJDNmeEm2I9AG5E2Z-sPJRgGxYcf466vkN5tLlY85Eiy5W9Ji1E-MriNXbp7pk5fWLyLSsBj3dF3RqmPSFfEF+ojazevmMsYZvAs3TPMMccUFxbj-InuPYLcQzHGVZMA+5Crnngl7YDAd+rIKJY+Ylq1gLCS-H7dSahqbI2Tu8lyZZVqL2+HiBKVphFWLpuVMJhR2pJmaMF0aabC9YkZlFa4Z0wxyHYdOcq2Ar2iyMPelh+dgTzSrvNJu-sjH0muQrKew43rMdifGTJ0N8pI28dlqOX96Vpy9PnPI7Ci5YPbkyoeak69j3tu2YGdCknN11Mo6O6L38xlHnaWcxZQF6nYOPMJzi2XyH0VPdTci95gtMPa7p5T7O8uy34pZ1SwH3I+AGYo5y23POzPUqaU+rkBs4dvPlYBqY+BxeK69t7zDHucc+t97yfHBt1d6+98hyV4v65s42UH708flMFyJQzj3ZbbeGKS727Vc1DNVSL4t41przV6RYk6z3P7g0+5r1LhrbrGOYZr6HrzRtDGwaddHmO9fkNpYA914uDP69t9uungHY-mtlozFthFA6005uLyQOhZf64FuKEWiEJa8C1nLUGWmD0a3A1BuoFAEN4RNphgZNt2Nr+dvRigftwkh0cnwp9YgYzhRkzFNOymHgb-P2IAsZVUM2YAwTSA9mXuSA-maAvmWKfCMWBAv0FAnJCMVAmUdySA5pLA5AYqAFR5fA5XD-LUA2Egigz1PSVAt9UAkAjkWsHbAZO2OKWseMAPW2SYYnM2TZIDXHA-XeRUQQsdW7Lg7KSMbyPcdDBHBMYnQSQyPDIAg-asMgJmGLQyMjDkB+SjIAnQszPyKA-CWApgkXX5FeeMWA1CaXcwpnEQXuPgxXIcBwoQwTZpNrEeKgSwuReMXcRQ+TOwiaORPg4jfwtTRgj6XkNQ6VK+TQ-TbQ0pXKfQ5hN+BBOA2KUw4rX5EieMeA6w5vHCPg6ZEQJwhBNoCdeUGZDwnIncTA7yAycLUnJZcCLpDQuLKI-2Vg4-XROItLKInQzLBI3nXLUbAQSAlAzI+HJReMFA-I4DarbZEQMWRw1HeBZY1w9Y0QlBaYniYqbyHrMIhY2Q89Vono+qCYgDcQaI9JIuOIixMYnQ+bB49Q+xZbVbA8HAjArwyYnxLJeMHAuY9lG2LJPggKYnUosEraMErYwpPxf41JXwqbQ4kE4nd7EIxFZEzA2sX7a4iHW4jaTyLwnQ0HDNF4hpbqGZXAykn4n9YnOKSkwEqrPg5kmZFYmwsOVk1w5pdwsQvg+kv3REinQ4lkkQPsLHU48pYU6k0nG8XEmVfEqhDnIY8tPQsku5fnXKIghEmkxlfXCQ0gjg1YmXFogUVJNkhrUFM0rkx5Hk-ZMXOKdFREpfPXMXZk9FdEgHYU4gg-C3OUolOIm3JIrkclIY53GlAUnlAUnUgZeVOKCgxktHJlJoylP3c0i7cPZALaDM205PdgzsePQU05YU+VZk+PD0-0xDKM93EQXEhIAMnVforkA1UM5hE1YoM1JpJ1XArs6MjlYNOKLshM4JKqaqHgp1NM3HccrkqcmEvXfszsIfCQ0IjZYNZkxcj0yUlcmgg-efCIjKIEYSQYdNZ47gHNUk3nLfHfEtC6LUIYG8+aHgU-OtdQbACGWEG-Ftd85tbGL81GdGbAftcEXfNgd-ctLLK5PjROP-cUAAv0e0ZqGsLkBCpdA-BChw5C9dW8tzeUDCndHCgMZY3Cw9YIhCgKIiiWMCggpCiDcA1khC0gyipdG0+ig2Ri8A1i+i8c3Cug0Yb0H01JZgjlO2G3PiuUPxTg2OJUYQ50EmdkxC-Ue0A-SaScVVAUPxbUESjKJsGQqShMHkBFISDZfinKCXaVYuQ88Aaud5IaKytAesexQw9CnjaqR5QSzuc3PxBwi3TgleXSrytlH1Lyy0Bw5SsTZeDyxTYIi3XcYScK0MKgKTXS4jWK+TFy1JTTUgnTIuCy2+P5VuaMRZXnVIiOBC8FASswiBMS0JeUbyo07I+0fSsoxq0o8FSBeUUK6ohqvxT5bqnyFK8gEiJKh2Rq5K9o0yheU0zFChCyvovKvkGhay4Y1hEigiqK8qrIkRaMe7KK8Suqzaq0QWKKgKrzZYlACLYIjqsQpRTS69Xqnrfqo43S69DBXRB606oXdUVJG4iy+4uap4uaszN41xD4h2Ui4a9a+HEEi3AKWqmw4E9SxqmG46+BGGy0AKS6zJBGvxNE6KqbB6qGiMHGjBA8wpcGkYX7TKvEiywkua0HRaszSHKi3ipm0gty2QzS7k2Ggo5kxqzm5GyZVks60nMSDGjZHgi3MU-UO60xB6nm5ZVMkaqmsWsSG05nSm+UiypUxalUgG5he5JpZizDG01yiqlFKW5SM0rm+YvU3Shi5quqy06MBqs00Wl05WdS903Gkmt2+KwQVXF68pWW42y2hGr6jPbK86ElOah3Aq+yqlcMyqYPBWiGr3H09S1iq2oEpMg622BW-mpXDO+0Vi12mOEsiWss3GjW3MmSxVX2q3WWjOs03PUygQGEQvZSQqkvDuuOguNsjs02LitvVXFOuvFy9S8czOpk1c3mie-OsOCe+0ccku7Oae8e5DSu8ylclyx1degOiOuc4erUXcymq8xU486OtfXW+xS8oC68w0ROslYMB8kALIeQX4DoAwQAMRBpAgZMhNAvgfg-hz9ABmEDMDkAZDAH6BAvkqmFFOEubvHWgsHhnRgebuGgQd1HvS6Wpgwb9DpSGXgZKL5kIboSftgbmVVC9G9GbrRNwbbHQZEHQafsTjSHYCECGnvSfuGmDRGAABM6ACwwRCwIQGBCw6BeG2IYLIAAIbYUBRSnRppn0O9Di5HJgFHeBUz1HWpb6LJuG9Jhpdy9YuB+BFR+QEqsyzGMpxBT7iIcHsHtZmHRBWG2B2HDYnZdZ9Ukw+GBH8whGRGxGJGcwpGZHvpvQtGrVlGt429nKtQtGQA26LIZYnUZZDGpwuAnxLGnZDotoxAqAEn34SHZlbZHG+BnHXGJrinQlhKeGQB+HBHhHRHxHJHB5pHh4051GKmqpInkV2nsNF7os6zIJOmA0k0EMqEI5LHH5vRMmNH4nUiqHbYRAFmpgSmynjNln3G+QyGam6nfGGmAnmmYBWnflq8BttnumNElHwLFQ4mC8LJlmX0yHUnS5HrLGsAj6cnZm7n-Im6RBaHVnfRXH-m3szSdmfG-HGnAm0Jgnh5RMumQXYmLnsI4X1H8dbmBo0Te8zTnmCS7zLHv9RxPnxAtU2AgA) и проверить сложение в симуляторе.
   Тот же текст схемы лежит в [sim/adder4.txt](sim/adder4.txt) (Файл → Импорт из текста).
2. Собрать плату ввода-вывода и четыре платы разряда по [assembly.md](assembly.md)
   и [wiring.md](wiring.md).
3. Проверять разряды по одному, начиная с младшего, по таблице истинности из assembly.md.
