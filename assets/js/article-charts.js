(() => {
  const chartElements = document.querySelectorAll("[data-article-chart]");

  if (!chartElements.length || typeof echarts === "undefined") {
    chartElements.forEach((figure) => {
      figure.querySelector(".article-chart__canvas").textContent = "图表加载失败，请刷新页面重试。";
    });
    return;
  }

  const charts = [];
  const numberFormatter = new Intl.NumberFormat();

  function palette() {
    const styles = getComputedStyle(document.documentElement);

    return {
      normal: styles.getPropertyValue("--article-chart-normal").trim(),
      problem: styles.getPropertyValue("--article-chart-problem").trim(),
      excluded: styles.getPropertyValue("--article-chart-excluded").trim(),
      text: styles.getPropertyValue("--article-chart-text").trim(),
      muted: styles.getPropertyValue("--article-chart-muted").trim(),
      grid: styles.getPropertyValue("--article-chart-grid").trim(),
      threshold: styles.getPropertyValue("--article-chart-threshold").trim(),
      tooltipBackground: styles.getPropertyValue("--article-chart-tooltip-bg").trim(),
      tooltipBorder: styles.getPropertyValue("--article-chart-tooltip-border").trim(),
    };
  }

  function optionFor(element, data) {
    const colors = palette();
    const compact = element.clientWidth < 560;
    const suffix = data.valueSuffix || "";

    return {
      animationDuration: 450,
      animationEasing: "cubicOut",
      aria: {
        enabled: true,
        decal: { show: false },
      },
      grid: {
        top: 18,
        right: compact ? 46 : 72,
        bottom: 48,
        left: compact ? 118 : 158,
      },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        backgroundColor: colors.tooltipBackground,
        borderColor: colors.tooltipBorder,
        textStyle: { color: colors.text },
        formatter(params) {
          const item = data.items[params[0].dataIndex];
          const detail = item.detail ? `<br>${item.detail}` : "";
          return `${item.label}<br><strong>${numberFormatter.format(item.value)}${suffix}</strong>${detail}`;
        },
      },
      xAxis: {
        type: "value",
        min: 0,
        max: data.xMax,
        splitNumber: compact ? 4 : 5,
        name: data.xUnit,
        nameLocation: "middle",
        nameGap: 30,
        nameTextStyle: { color: colors.muted },
        axisLabel: {
          color: colors.muted,
          formatter(value) {
            if (data.axisFormat === "percent") {
              return `${value}%`;
            }
            if (compact && value >= 1000) {
              return `${value / 1000}k`;
            }
            return numberFormatter.format(value);
          },
        },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: {
          lineStyle: { color: colors.grid },
        },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: data.items.map((item) => item.label),
        axisLabel: {
          color: colors.text,
          fontSize: compact ? 11 : 13,
          width: compact ? 108 : 146,
          overflow: "truncate",
        },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [{
        type: "bar",
        barMaxWidth: 28,
        data: data.items.map((item) => ({
          value: item.value,
          itemStyle: {
            color: colors[item.group] || colors.normal,
            borderRadius: [0, 4, 4, 0],
          },
        })),
        label: {
          show: true,
          position: "right",
          color: colors.text,
          fontWeight: 600,
          formatter(params) {
            return `${numberFormatter.format(params.value)}${suffix}`;
          },
        },
        markLine: data.threshold ? {
          silent: true,
          symbol: "none",
          lineStyle: {
            color: colors.threshold,
            type: "dashed",
            width: 1.5,
          },
          label: {
            color: colors.threshold,
            formatter: data.thresholdLabel,
            position: "insideStartTop",
            rotate: 0,
          },
          data: [{ xAxis: data.threshold }],
        } : undefined,
      }],
    };
  }

  async function renderChart(figure) {
    const canvas = figure.querySelector(".article-chart__canvas");
    const response = await fetch(figure.dataset.chartSrc);

    if (!response.ok) {
      throw new Error(`Failed to load chart data: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const chart = echarts.init(canvas, null, { renderer: "svg" });

    chart.setOption(optionFor(canvas, data));
    charts.push({ chart, canvas, data });
    resizeObserver.observe(canvas);
  }

  const resizeObserver = new ResizeObserver((entries) => {
      entries.forEach((entry) => {
        const current = charts.find(({ canvas }) => canvas === entry.target);
        if (current) {
          current.chart.resize();
          current.chart.setOption(optionFor(current.canvas, current.data), true);
        }
      });
    });

  Promise.all([...chartElements].map(renderChart)).catch((error) => {
    console.error(error);
    chartElements.forEach((figure) => {
      const canvas = figure.querySelector(".article-chart__canvas");
      if (!canvas.querySelector("svg")) {
        canvas.textContent = "图表加载失败，请刷新页面重试。";
        canvas.classList.add("article-chart__canvas--error");
      }
    });
  });

  new MutationObserver(() => {
    charts.forEach(({ chart, canvas, data }) => {
      chart.setOption(optionFor(canvas, data), true);
    });
  }).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class", "data-theme"],
  });
})();
