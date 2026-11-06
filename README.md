# Centipede — Arcade Remix

Clon modular de Centipede con una versión nativa en Python/Pygame y una versión web estática en HTML5 Canvas. Ambas incluyen estilos retro y cyberpunk, hongos destructibles, ciempiés divisibles, variantes especiales, tótems, HUD, pausa y oleadas.

## Versión web — GitHub Pages

`index.html` es autónomo: contiene el CSS y JavaScript del juego, no depende de paquetes, imágenes ni servicios externos y puede servirse directamente desde GitHub Pages.

1. Sube este repositorio a GitHub con `index.html` en la raíz.
2. En GitHub, abre **Settings → Pages**.
3. En **Build and deployment**, elige **Deploy from a branch**, selecciona la rama y la carpeta **/(root)**, y guarda.
4. Abre la URL que GitHub Pages muestre en esa sección.

No hay proceso de compilación ni configuración de frameworks. El juego también funciona abriendo `index.html` directamente en un navegador moderno.

### Controles web

- **Flechas** o **WASD**: mover la nave.
- **Espacio** o clic/toque sobre el área de juego: disparar; mantener para fuego repetido.
- **P**, **Shift** o **Esc**: pausar y reanudar.
- **T** o el botón **Cambiar estilo**: alternar `RETRO_80S` y `MODERNO`.
- **Menú**: `1` o Enter para jugar, `2` para salir (en web se indica cerrar la pestaña); se puede seleccionar con el ratón/toque.
- **Game Over**: Enter para volver a jugar.
- En pantallas táctiles aparecen controles direccionales y de disparo.

La puntuación máxima se guarda localmente en el navegador cuando el almacenamiento está disponible.

## Versión nativa Python/Pygame

Requiere Python 3.10 o posterior y Pygame 2.5 o posterior.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

En ChromeOS/Linux se requiere una sesión gráfica disponible para Pygame.

## Estructura

- `index.html`: versión web autocontenida, lista para publicar en GitHub Pages.
- `config.py`: constantes, paletas, coordenadas y estados de la versión nativa.
- `blocks.py`: campo de hongos, daño y esporas.
- `player.py`: nave, movimiento y proyectiles.
- `enemy.py`: cadenas de ciempiés, división y tótems.
- `interface.py`: HUD, menú y superposiciones.
- `main.py`: bucle principal e integración de la versión nativa.
