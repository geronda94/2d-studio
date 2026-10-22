<template>
 <div class="logo-3d-container group">
 <div class="logo-key-wrapper">
 <div class="keycap-solid">
 <div class="keycap-svg-layer">
 <svg width="180" height="90" viewBox="0 0 180 90" fill="none" xmlns="http://www.w3.org/2000/svg">
 <defs>
 <linearGradient id="glow-grad" x1="0%" y1="0%" x2="100%" y2="100%">
 <stop offset="0%" stop-color="var(--color-secondary)" />
 <stop offset="100%" stop-color="var(--color-primary)" />
 </linearGradient>
 </defs>
 <!-- Текст идеально по центру -->
 <text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" font-family="'Space Grotesk', sans-serif" font-weight="700" font-size="42" fill="var(--text-primary)" letter-spacing="1">
 <tspan>IT</tspan><tspan fill="url(#glow-grad)">2</tspan><tspan>B</tspan>
 </text>
 </svg>
 </div>
 </div>
 </div>
 </div>
</template>

<style scoped>
.logo-3d-container {
 display: inline-block;
 perspective: 1000px;
 cursor: pointer;
}

.logo-key-wrapper {
 /* Сделали угол более пологим, чтобы занимать меньше высоты */
 transform: rotateX(18deg) rotateY(10deg) rotateZ(-3deg);
 transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
 transform-style: preserve-3d;
}

.group:hover .logo-key-wrapper {
 transform: rotateX(18deg) rotateY(10deg) rotateZ(-3deg) translate(-3px, 3px);
}

.keycap-solid {
 width: 180px;
 height: 90px;
 border-radius: 20px;
 background: linear-gradient(135deg, #1E293B, #0F172A);
 position: relative;
 /* Убираем border и используем inset тень + outline для сглаживания рваных краев */
 outline: 1px solid transparent;
 box-shadow: 
 inset 0 0 0 2px rgb(var(--color-secondary-rgb) / 0.4),
 -1px 1px 0px #1a2231,
 -1px 2px 0px #171f2d,
 -2px 3px 0px #131924,
 -2px 4px 0px #0e131a,
 -3px 5px 0px #080a0d,
 -3px 6px 0px #030404,
 -3px 7px 5px rgb(var(--color-primary-rgb) / 0.5), /* Мягкое неоновое свечение в статике */
 -10px 15px 25px rgba(0, 0, 0, 0.7); /* Тень на поверхности */
 transition: box-shadow 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.group:hover .keycap-solid {
 box-shadow: 
 inset 0 0 0 2px rgb(var(--color-secondary-rgb) / 0.8),
 -1px 1px 0px #1c2536,
 -1px 2px 0px #151c28,
 -2px 3px 0px #0c1016,
 -2px 4px 15px rgb(var(--color-primary-rgb) / 0.9), /* Усиленное свечение при нажатии */
 -5px 10px 20px rgba(0, 0, 0, 0.8);
}

.keycap-solid::before {
 content: '';
 position: absolute;
 inset: 8px;
 border-radius: 12px;
 background: linear-gradient(135deg, rgb(var(--text-primary-rgb) / 0.05), rgba(0,0,0,0.3));
 box-shadow: inset 0 6px 10px rgba(0,0,0,0.6), inset 0 -2px 5px rgb(var(--text-primary-rgb) / 0.15);
 border: 1px solid rgba(0,0,0,0.8);
 z-index: 1;
}

.keycap-svg-layer {
 position: absolute;
 inset: 0;
 z-index: 2;
 pointer-events: none;
 transition: filter 0.5s ease;
 filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.5));
}

.group:hover .keycap-svg-layer {
 filter: drop-shadow(0 0 12px rgb(var(--color-secondary-rgb) / 0.6));
}
</style>
