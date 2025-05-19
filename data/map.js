function toggleFullscreen() {
    const container = document.getElementById('map-container');
    container.classList.toggle('fullscreen');
    const btn = document.querySelector('.fullscreen-btn');
    btn.textContent = container.classList.contains('fullscreen') ? '⮽' : '⛶';
    
    // Обновляем размеры SVG при изменении размера контейнера
    const svg = d3.select('svg');
    svg.attr('width', container.offsetWidth)
       .attr('height', container.offsetHeight);
    
    // Обновляем проекцию
    const config = {
        width: container.offsetWidth,
        height: container.offsetHeight,
        center: [47.0, 55.5],
        scale: 8000
    };
    
    projection.center(config.center)
             .scale(config.scale)
             .translate([config.width / 2, config.height / 2]);
    
    // Перерисовываем карту
    g.selectAll('path').attr('d', path);
    markers.selectAll('.channel-node').each(function() {
        const channel = d3.select(this).datum();
        const [x, y] = projection([channel.lon, channel.lat]);
        d3.select(this).attr('transform', `translate(${x}, ${y})`);
    });
}

// Конфигурация
const config = {
    width: document.getElementById('map-container').offsetWidth,
    height: document.getElementById('map-container').offsetHeight,
    center: [47.0, 55.5],
    scale: 8000
};

// Создаем SVG
const svg = d3.select('#map-container')
    .append('svg')
    .attr('width', config.width)
    .attr('height', config.height);

// Создаем группу для карты
const g = svg.append('g');

// Создаем проекцию
const projection = d3.geoMercator()
    .center(config.center)
    .scale(config.scale)
    .translate([config.width / 2, config.height / 2]);

const path = d3.geoPath().projection(projection);

// Добавляем границы Чувашии
const chuvashiaData = CHUVASHIA_DATA;
g.append('path')
    .datum(chuvashiaData.features[0])
    .attr('d', path)
    .attr('fill', '#ffff00')
    .attr('fill-opacity', 0.1)
    .attr('stroke', '#000000')
    .attr('stroke-width', 2);

// Создаем тултип
const tooltip = d3.select('#map-container')
    .append('div')
    .attr('class', 'tooltip');

// Данные каналов
const channels = CHANNELS_DATA;

// Создаем группу для маркеров
const markers = g.append('g')
    .attr('class', 'markers');

// Создаем force simulation
const simulation = d3.forceSimulation(channels)
    .force('center', d3.forceCenter(config.width / 2, config.height / 2))
    .force('charge', d3.forceManyBody().strength(2))
    .force('collide', d3.forceCollide().radius(d => d.size * 1.5))
    .force('x', d3.forceX(config.width / 2).strength(0.05))
    .force('y', d3.forceY(config.height / 2).strength(0.05))
    .on('tick', function() {
        markers.selectAll('.channel-node')
            .attr('transform', function(d) {
                // Получаем границы Чувашии
                const bounds = path.bounds(chuvashiaData.features[0]);
                
                // Ограничиваем движение точками в пределах границ
                const x = Math.max(bounds[0][0] + d.size, Math.min(bounds[1][0] - d.size, d.x));
                const y = Math.max(bounds[0][1] + d.size, Math.min(bounds[1][1] - d.size, d.y));
                
                // Проверяем, находится ли точка внутри границ
                const point = projection.invert([x, y]);
                const isInside = d3.geoContains(chuvashiaData.features[0], point);
                
                if (!isInside) {
                    // Если точка вышла за границы, возвращаем её на предыдущую позицию
                    d.x = d.px || config.width / 2;
                    d.y = d.py || config.height / 2;
                } else {
                    // Обновляем позицию
                    d.x = x;
                    d.y = y;
                    // Сохраняем текущую позицию
                    d.px = x;
                    d.py = y;
                }
                
                return 'translate(' + d.x + ', ' + d.y + ')';
            });
    });

// Добавляем начальное размещение точек
channels.forEach(d => {
    // Получаем случайную точку внутри границ Чувашии
    const bounds = path.bounds(chuvashiaData.features[0]);
    let x, y, point;
    do {
        x = bounds[0][0] + Math.random() * (bounds[1][0] - bounds[0][0]);
        y = bounds[0][1] + Math.random() * (bounds[1][1] - bounds[0][1]);
        point = projection.invert([x, y]);
    } while (!d3.geoContains(chuvashiaData.features[0], point));
    
    d.x = x;
    d.y = y;
    d.px = x;
    d.py = y;
});

// Функция для создания маркера
function createMarker(channel) {
    // Создаем группу для маркера
    const marker = markers.append('g')
        .attr('class', 'channel-node')
        .style('opacity', 0)
        .datum(channel);

    // Добавляем изображение
    marker.append('image')
        .attr('x', d => -d.size)
        .attr('y', d => -d.size)
        .attr('width', d => d.size * 2)
        .attr('height', d => d.size * 2)
        .attr('href', d => d.logo_url || '')
        .attr('clip-path', d => `circle(${d.size}px at ${d.size}px ${d.size}px)`)
        .style('display', d => d.logo_url ? 'block' : 'none');

    // Добавляем круг с тенью (если нет изображения)
    marker.append('circle')
        .attr('r', d => d.size)
        .attr('fill', '#4CAF50')
        .attr('filter', 'drop-shadow(0 0 5px rgba(0,0,0,0.2))')
        .style('display', d => d.logo_url ? 'none' : 'block');

    // Добавляем интерактивность
    marker
        .on('mouseover', function(event, d) {
            d3.select(this)
                .transition()
                .duration(300)
                .attr('transform', 'translate(' + d.x + ', ' + d.y + ') scale(1.2)');

            tooltip
                .style('opacity', 1)
                .html(`
                    <h3>${d.name}</h3>
                    <p>${d.description}</p>
                    <p>Подписчиков: ${d.members_count || 'Нет данных'}</p>
                    <p>Сообщений: ${d.messages_count || 'Нет данных'}</p>
                    ${d.username ? `<a href="https://t.me/${d.username}" target="_blank" style="color: #4CAF50; text-decoration: none;">Перейти в канал</a>` : ''}
                `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function(event, d) {
            d3.select(this)
                .transition()
                .duration(300)
                .attr('transform', 'translate(' + d.x + ', ' + d.y + ')');

            tooltip.style('opacity', 0);
        })
        .on('click', function(event, d) {
            // Центрируем карту на выбранном канале
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity
                    .translate(config.width / 2, config.height / 2)
                    .scale(4)
                    .translate(-d.x, -d.y));
        });

    // Анимация появления
    marker.transition()
        .duration(1000)
        .delay(Math.random() * 1000)
        .style('opacity', 1);
}

// Создаем маркеры для всех каналов
channels.forEach(createMarker);

// Добавляем зум и панорамирование
const zoom = d3.zoom()
    .scaleExtent([1, 8])
    .on('zoom', (event) => {
        g.attr('transform', event.transform);
    });

svg.call(zoom);

// Добавляем обработчики для списка каналов
document.querySelectorAll('.channel-item').forEach(item => {
    item.addEventListener('click', function() {
        const channelName = this.querySelector('.channel-title').textContent;
        const channel = channels.find(c => c.name === channelName);
        if (channel) {
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity
                    .translate(config.width / 2, config.height / 2)
                    .scale(4)
                    .translate(-channel.x, -channel.y));
        }
    });
}); 