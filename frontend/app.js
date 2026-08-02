import { floors } from "./floor-zone.js";

const mapWrapper = document.getElementById("mapWrapper");
const floorImage = document.getElementById("floorImage");
const zoneInfo = document.getElementById("zoneInfo");
const floorInfo = document.getElementById("floorInfo");



const API_BASE = "";      // backend api local url http://127.0.0.1:8000




async function renderFloor(floorKey) {
  const floor = floors[floorKey];
  floorImage.src = floor.image;

  mapWrapper.querySelectorAll(".map-zone").forEach(el => el.remove());


try{
    const response = await fetch(`${API_BASE}/env/environmental-data?zone=${floor.overview.zone_id}`);

    if (!response.ok || response == null) {
        floorInfo.innerHTML = `
            <h3>${floor.overview.name} Floor Overview</h3>
            <p>🌡 Temperature: ${floor.overview.temperature} °C</p>
            <p>🔊 Noise: ${floor.overview.noise} dB</p>
            <p>💧 Humidity: ${floor.overview.humidity}%</p>
        `;
    }
    else if (response.ok){
        const data = await response.json();

        floorInfo.innerHTML = `
            <h3>${floor.overview.name} Floor Overview</h3>
            <p>🌡 Temperature: ${data.temperature_c} °C</p>
            <p>🔊 Noise: ${data.noise_db} dB</p>
            <p>💧 Humidity: ${data.humidity_percent}%</p>
        `;
    }
    } catch (error){
        console.error(error);
}


  floor.zones.forEach(zone => {
    const div = document.createElement("div");
    div.className = "map-zone";
    div.style.left = zone.left;
    div.style.top = zone.top;
    div.style.width = zone.width;
    div.style.height = zone.height;
    div.dataset.id = zone.id;

    if (zone.recommended) {
        div.classList.add("recommended-zone");
    }

    if (zone.type == "computing") {
        div.classList.add("pc-zone");
    }
    else if (zone.type == "collaborative") {
        div.classList.add("hubs");
    } 

    let emoji = "";

    if (zone.type === "computing") {
    emoji = "🖥️";
    } else if (zone.type === "collaborative") {
    emoji = "👥";
    } else if (zone.type === "reading") {
    emoji = "📚";
    }


    if (zone.recommended) {
    emoji = "⭐";
    }
    
    if (emoji) {
    const emojiElement = document.createElement("span");
    emojiElement.className = "zone-emoji";
    emojiElement.textContent = emoji;
    div.appendChild(emojiElement);
    }


    div.addEventListener("click", (e) => {
      e.stopPropagation();
      showInfo(zone);
    });

    mapWrapper.appendChild(div);
  });
}








renderFloor("ground");
document.getElementById("floorSelect").addEventListener("change", (event)=>{
    const selectedValue = event.target.value;
    renderFloor(selectedValue);
});





const occupancy_mes = document.getElementById("occupancy_mes");
const prediction_mes = document.getElementById("forecast_mes");

const current_occupancy = document.getElementById("current_occupancy");
const predicted_occupancy = document.getElementById("predicted_occupancy");
// fetch data from backend api



let isLoadingDashboard = false;

async function loadDashboard(){

    if (isLoadingDashboard) return;
    isLoadingDashboard = true;              // loading lock

    try{
    const [occupancyRes, predictionRes] = await Promise.all([
      fetch(`${API_BASE}/occupancy/current`),
      fetch(`${API_BASE}/prediction/next-hour`)
    ]);

    if (!occupancyRes.ok || !predictionRes.ok) {
      throw new Error("API request failed");
    }

    const occupancyJSON = await occupancyRes.json();
    const predictionJSON = await predictionRes.json();

    current_occupancy.textContent = `${occupancyJSON.current_occupancy}+ `;
    predicted_occupancy.textContent = `${predictionJSON.predicted_occupancy}+ `;

    occupancy_mes.textContent = `${occupancyJSON.message} `;
    prediction_mes.textContent = `Predicted peak at ${predictionJSON.predicted_peak} `;

    updateOccupancy(occupancyJSON.current_occupancy);

    } catch (error){
        console.error(error);
        occupancy_mes.textContent = "Failed to load data";
        prediction_mes.textContent = "Failed to load data";

    } finally {
        isLoadingDashboard = false;
  }
}


const timeID = setInterval(loadDashboard, 1000);   // 1 update per second




async function showInfo(zone) {

    try{
        const response = await fetch(`${API_BASE}/env/environmental-data?zone=${zone.id}`);

        if (!response.ok) {
                zoneInfo.innerHTML = `
                <h3>${zone.name}</h3>
                <p>📚 Type: </p>
                <p>🌡 Temperature: °C</p>
                <p>🔊 Noise: dB</p>
                <p>💧 Humidity: %</p>
            `;
            return
        }


        const data = await response.json();

        zoneInfo.innerHTML = `
            <h3>${zone.name}</h3>
            <p>📚 Type: ${zone.type}</p>
            <p>🌡 Temperature: ${data.temperature_c} °C</p>
            <p>🔊 Noise: ${data.noise_db} dB</p>
            <p>💧 Humidity: ${data.humidity_percent}%</p>
        `;


        } catch (error){
            console.error(error);
            zoneInfo.innerHTML = `
            <h3>${zone.name}</h3>
            <p>📚 Type:</p>
            <p>🌡 Temperature: °C</p>
            <p>🔊 Noise: dB</p>
            <p>💧 Humidity: %</p>
            `;
    }

}





let occupancyChart;
let forecastChart;
const occupancyCtx = document.getElementById("occupancyChart");
const forecastCtx = document.getElementById("forecastChart");

function createGradient(ctx, chartArea, colorTop, colorBottom) {
  const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  gradient.addColorStop(0, colorTop);
  gradient.addColorStop(1, colorBottom);
  return gradient;
}






const labels1 = ["8 AM", "10 AM", "12 PM", "2 PM","4 PM", "6 PM", "8 PM", "10 PM"];   // Monday to Friday
const labels2 = ["8 AM", "10 AM", "12 PM", "2 PM","4 PM", "6 PM", "7 PM"];           // Saturday
const labels3 = ["11 AM", "12 AM", "1 PM","2 PM", "3 PM", "4 PM", "5 PM", "6 PM"];  // Sunday


function getHongKongWeekday() {
  const weekdayText = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Hong_Kong",
    weekday: "short"
  }).format(new Date());

  const weekdayMap = {
    Sun: 0,
    Mon: 1,
    Tue: 2,
    Wed: 3,
    Thu: 4,
    Fri: 5,
    Sat: 6
  };

  return weekdayMap[weekdayText];
}


function getTodayChartHours() {
  return Array.from({ length: 17 }, (_, index) => index + 7);
}

function formatHour(hour) {
  if (hour === 0) return "12 AM";
  if (hour === 12) return "12 PM";

  return hour > 12
    ? `${hour - 12} PM`
    : `${hour} AM`;
}



function isLibraryOpenHour(hour, weekday) {
  // Monday to Friday
  // 08:20:00–21:59:59 有效
  // 08 bucket 代表 8:20–8:59:59
  if (weekday >= 1 && weekday <= 5) {
    return hour >= 8 && hour <= 21;
  }

  // Saturday
  // 08:20:00–18:59:59 有效
  if (weekday === 6) {
    return hour >= 8 && hour <= 18;
  }

  // Sunday
  // 11:00:01–18:59:59 有效
  if (weekday === 0) {
    return hour >= 11 && hour <= 18;
  }

  return false;
}


function buildChartData(series, hours, weekday, cutoffHour = null) {
  const occupancyByHour = new Map(
    series.map(item => [
      Number(item.time.split(":")[0]),
      item.occupancy
    ])
  );

  let previousOccupancy = 0;

  return hours.map(hour => {
    if (cutoffHour !== null && hour > cutoffHour) {
      return null;
    }

    if (!isLibraryOpenHour(hour, weekday)) {
      return 0;
    }

    if (occupancyByHour.has(hour)) {
      previousOccupancy = occupancyByHour.get(hour);
    }
    return previousOccupancy;
  });
}



 async function initCharts(){

    try{
    const [todaySeries, lastSeries] = await Promise.all([
      fetch(`${API_BASE}/occupancy/today`),
      fetch(`${API_BASE}/occupancy/last-week`)
    ]);

    if (!todaySeries.ok || !lastSeries.ok) {
      throw new Error("API request failed");
    }

    const todayJSON = await todaySeries.json();
    const lastJSON = await lastSeries.json();



const chartHours = getTodayChartHours();

const nowHKT = new Date().toLocaleString("en-US", {
  timeZone: "Asia/Hong_Kong",
  hour: "2-digit",
  hourCycle: "h23"
});

const currentHour = Number(nowHKT);

const currentHourIndex = chartHours.indexOf(currentHour);

const shouldShowCurrentMarker = currentHourIndex >= 0;

    const occupancyLabels = chartHours.map(hour =>`${String(hour).padStart(2, "0")}:00`);


const weekday = getHongKongWeekday();

const todayOccupancyData = buildChartData(
  todayJSON.series,
  chartHours,
  weekday,
  currentHour
);

const lastWeekOccupancyData = buildChartData(
  lastJSON.series,
  chartHours,
  weekday
);



    occupancyChart = new Chart(occupancyCtx, {
        type: "line",
        data: {
            labels: occupancyLabels,
            datasets: [
                {
                    label: "Today",
                    data: todayOccupancyData,
                    borderColor: "#f0c53f",
                    backgroundColor: (context) => {
                        const { chart } = context;
                        const { ctx, chartArea } = chart;
                        if (!chartArea) return "rgba(255, 214, 92, 0.28)";
                        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                        gradient.addColorStop(0, "rgba(255, 214, 92, 0.55)");
                        gradient.addColorStop(1, "rgba(255, 214, 92, 0.06)");
                        return gradient;
                    },
                    fill: true,
                    tension: 0.42,
                    borderWidth: 1,
pointRadius: (context) => {
  return (
    shouldShowCurrentMarker &&
    context.dataIndex === currentHourIndex
  ) ? 5 : 0;
},
  pointHoverRadius: 5,
  pointBackgroundColor: "#ffffff",
  pointBorderColor: "#f0c53f",
  pointBorderWidth: 1,
  spanGaps: false,
  order: 1
                },
                {
                    label: "Last Week",
                    data: lastWeekOccupancyData,
                    borderColor: "rgba(171,145,59,0.78)",
                    backgroundColor: "rgba(120, 96, 28, 0.38)",
                    fill: true,
                    tension: 0.42,
                    borderWidth: 1,
                    pointRadius: 0,
                    order: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: { top: 4, right: 6, bottom: 0, left: 0 }
            },
            plugins: {
                legend: {
                position: "top",
                align: "end",
                labels: {
                    color: "#f7f4ff",
                    usePointStyle: true,
                    pointStyle: "circle",
                    boxWidth: 6,
                    boxHeight: 6,
                    padding: 10,
                    font: {size: 10, weight: "600"}
                }
                },
                tooltip: {enabled: true},
verticalLinePlugin: {
  index: currentHourIndex,
  datasetIndex: 0,
  color: "rgba(255,255,255,0.9)"
}
            },
            scales: {
                x: {
                    offset: false,
                    ticks: { 
                        color: "rgba(255,255,255,0.9)",
                        font: {size: 9, weight: "600"},
                        grid: { display: false },
                        maxRotation: 0,
                        minRotation: 0,
                        padding: 6,
                        autoSkip: false,
                        callback: function(value, index) {
                            const hour = chartHours[index];
                            if (hour % 2 === 1) {return formatHour(hour);}
                            return "";
                        }
                    },
                    grid: {
                        drawOnChartArea: false,
                        drawTicks: true,
                        tickLength: 8,
                        color: "rgba(255,255,255,0.9)",
                        lineWidth: 1
                    },
                    border: {
                        display: true,
                        color: "rgba(255,255,255,0.95)",
                        width: 1
                    }
                },

                y: {
                    display: false,
                    beginAtZero: true,
                    grid: { display: false },
                    border: { display: false }
                }
            },
            elements: {line: {borderWidth: 1}}
        }});




    forecastChart = new Chart(forecastCtx, {
    type: "line",
    data: {
        labels: ["12 PM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM"],
        datasets: [
        {
            label: "Forecast",
            data: [18, 17, 16, 20, 78, 110, 130, 100],
            borderColor: "#c8b8ff",
            backgroundColor: (context) => {
            const { chart } = context;
            const { ctx, chartArea } = chart;
            if (!chartArea) return "rgba(200, 184, 255, 0.24)";
            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradient.addColorStop(0, "rgba(200, 184, 255, 0.42)");
            gradient.addColorStop(1, "rgba(200, 184, 255, 0.06)");
            return gradient;
            },
            fill: true,
            tension: 0.42,
            borderWidth: 1,
            pointRadius: [0, 0, 0, 0, 4, 0, 0],
            pointHoverRadius: 4,
            pointBackgroundColor: "#ffffff",
            pointBorderColor: "#c8b8ff",
            pointBorderWidth: 1,
            spanGaps: false
        }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
        padding: { top: 4, right: 6, bottom: 0, left: 0 }
        },
        plugins: {
        legend: {
            position: "top",
            align: "end",
            labels: {
            color: "#f7f4ff",
            usePointStyle: true,
            pointStyle: "circle",
            boxWidth: 6,
            boxHeight: 6,
            padding: 10,
            font: {
                size: 10,
                weight: "600"
            }
            }
        },
        tooltip: {
            enabled: true
        },
        verticalLinePlugin: {
            index: 4,          // 4 PM
            datasetIndex: 0,
            color: "rgba(255,255,255,0.78)"
        }
        },
        scales: {
        x: {
            offset: false,
            ticks: {
            color: "rgba(255,255,255,0.9)",
            font: {
                size: 9,
                weight: "600"
            },
            maxRotation: 0,
            minRotation: 0,
            padding: 6,
            autoSkip: false
            },
            grid: {
            drawOnChartArea: false,
            drawTicks: true,
            tickLength: 8,
            color: "rgba(255,255,255,0.9)",
            lineWidth: 1
            },
            border: {
            display: true,
            color: "rgba(255,255,255,0.95)",
            width: 1
            }
        },
        y: {
            display: false,
            beginAtZero: true,
            grid: { display: false },
            border: { display: false }
        }
        },
        elements: {
        line: {
            borderWidth: 1
        }
        }
    }
    });

    } catch (error){
        console.error(error);
    } 



}


const verticalLinePlugin = {
  id: "verticalLinePlugin",

  beforeDatasetsDraw(chart, args, pluginOptions) {
    const { ctx, chartArea } = chart;

    const activeIndex = pluginOptions.index;
    const datasetIndex = pluginOptions.datasetIndex ?? 0;

    // 例如凌晨 2 AM：
    // currentHourIndex = -1
    // chart 不顯示 marker
    if (
      !Number.isInteger(activeIndex) ||
      activeIndex < 0
    ) {
      return;
    }

    const meta = chart.getDatasetMeta(datasetIndex);
    const point = meta?.data?.[activeIndex];

    if (!point) {
      return;
    }

    const pointRadius = 4;
    const lineStartY = point.y + pointRadius + 4;

    ctx.save();

    // Vertical line
    ctx.beginPath();
    ctx.moveTo(point.x, lineStartY);
    ctx.lineTo(point.x, chartArea.bottom);
    ctx.lineWidth = 1;
    ctx.strokeStyle =
      pluginOptions.color || "rgba(255,255,255,0.85)";
    ctx.stroke();

    // Inner glow
    ctx.beginPath();
    ctx.arc(point.x, point.y, 9, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255,255,255,0.12)";
    ctx.fill();

    // Outer glow
    ctx.beginPath();
    ctx.arc(point.x, point.y, 15, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255,255,255,0.08)";
    ctx.fill();

    ctx.restore();
  }
};

Chart.register(verticalLinePlugin);


loadDashboard();
initCharts();










// Cookie and preference


function setCookie(name, value, days = 180) {
  const maxAge = days * 24 * 60 * 60;                 // browser will save document.cookie
  document.cookie = `${name}=${encodeURIComponent(value)};             
                     path=/; 
                     max-age=${maxAge}; 
                     samesite=lax`;
}


function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}


async function savePreferenceCookie(pref) {                   // pass pref to backend and save in frontend cookie
  const res = await fetch("/api/preferences", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pref)                              
  });

  if (!res.ok){
    throw new Error("save failed");
  }
  setCookie("cc_pref", JSON.stringify(pref), 180);
  console.log(pref);
}




function parsePreferenceCookie() {
  const raw = getCookie("cc_pref");
  if (!raw) return null;

  const [study_preference, preferred_floor] = raw.split("|");
  if (!study_preference || !preferred_floor) return null;

  return { study_preference, preferred_floor };
}




// asking for preference
const preferenceModal = document.getElementById("preferenceModal");
const close = document.getElementById("closePreferenceModal");
const skip = document.getElementById("skipPreference");
const save = document.getElementById("savePreference");


function closeModal() {preferenceModal.classList.add("hidden");}
function showModal() {;preferenceModal.classList.remove("hidden");}

close.addEventListener("click", closeModal);

document.getElementById("editPreferenceBtn").addEventListener("click", showModal);

document.addEventListener("DOMContentLoaded", () => {      // checking cookie before showing after loading
    const savedPref = parsePreferenceCookie();
    if (savedPref) {closeModal();} else {showModal();}
});


skip.addEventListener("click", async () => {
    const studyPreference = document.getElementById("studyPreference").value;
    const preferredFloor = document.getElementById("preferredFloor").value;
    const pref = {                       //JSON
      study_preference: "N/A",
      preferred_floor: "N/A"
    }
    try {
      await savePreferenceCookie(pref);
      closeModal();

    } catch (err) {
      console.error(err);
      alert("Failed to save preference.");
    }

    closeModal();
});


save.addEventListener("click", async () => {
    const studyPreference = document.getElementById("studyPreference").value;
    const preferredFloor = document.getElementById("preferredFloor").value;

    if (!studyPreference || !preferredFloor) {
        alert("Please select both study preference and preferred floor.");
        return;
    }

    const pref = {                       //JSON
      study_preference: studyPreference,
      preferred_floor: preferredFloor
    };

    try {
      await savePreferenceCookie(pref);
    } catch (err) {
      console.error(err);
      alert("Failed to save preference.");
    }
    document.getElementById("floorSelect").value = preferredFloor;
    renderFloor(preferredFloor);

    closeModal();
});



// real time keep checking the latest statistics (setTimeInterval) + data structure design




const TOTAL_CAPACITY = 500;

function getOccupancyBarColor(percent) {
  if (percent < 60) {
    return 'linear-gradient(90deg, #0d7ef2 0%, #35b0ff 100%)';
  }
  if (percent < 80) {
    return 'linear-gradient(90deg, #0d7ef2 0%, #2fa8ff 45%, #ffd338 100%)';
  }
  if (percent < 90) {
    return 'linear-gradient(90deg, #2fa8ff 0%, #ffd338 55%, #f39b20 100%)';
  }
  return 'linear-gradient(90deg, #2fa8ff 0%, #ffd338 45%, #f39b20 72%, #d93a2f 100%)';
}

function updateOccupancy(count) {
  const percent = Math.min(100, Math.round((count / TOTAL_CAPACITY) * 100));

  document.getElementById("current_occupancy").textContent = `${count}+`;
  document.getElementById("occupancy_rate_text").textContent = `${count}/${TOTAL_CAPACITY} (${percent}%)`;

  const fill = document.getElementById("occupancy_rate_fill");
  fill.style.width = `${percent}%`;
  fill.style.background = getOccupancyBarColor(percent);
}





function updateHKTClock() {
  const now = new Date();
  const time = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Hong_Kong',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  }).format(now);

  document.getElementById('occupancy_clock').textContent = `${time}`;
}

updateHKTClock();
setInterval(updateHKTClock, 1000);