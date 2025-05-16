NioApp = function(c, u, a) {
    "use strict";
    var t = u(".chart-data"),
        o = u(".chart-data-s2"),
        n = u(".chart-data-s1");
    c.Chart = {};
    var h = u(a);
    return c.Chart.ChartJs = function() {
        c.Chart.ChartJs.Doughnut = function(a, t, o, n, e, s) {
            if (u("#" + a).length) {
                var r = document.getElementById(a).getContext("2d"),
                    i = new Chart(r, {
                        type: "doughnut",
                        data: {
                            labels: t,
                            datasets: [{
                                label: "949",
                                lineTension: 0,
                                backgroundColor: o,
                                borderColor: e,
                                borderWidth: 2,
                                hoverBorderColor: e,
                                data: n
                            }]
                        },
                        options: {
                            legend: {
                                display: !1,
                                labels: {
                                    boxWidth: 10,
                                    fontColor: "#000"
                                }
                            },
                            rotation: -2,
                            cutoutPercentage: s,
                            responsive: !0,
                            maintainAspectRatio: !1,
                            tooltips: {
                                callbacks: {
                                    title: function(a, t) {
                                        return t.labels[a[0].index]
                                    },
                                    label: function(a, t) {
                                        return t.datasets[0].data[a.index] + " %"
                                    }
                                },
                                backgroundColor: "#eff6ff",
                                titleFontSize: 13,
                                titleFontColor: "#6783b8",
                                titleMarginBottom: 10,
                                bodyFontColor: "#9eaecf",
                                bodyFontSize: 14,
                                bodySpacing: 4,
                                yPadding: 15,
                                xPadding: 15,
                                footerMarginTop: 5,
                                displayColors: !1
                            }
                        }
                    });
                h.on("resize", function() {
                    i.resize()
                })
            }
        }, c.Chart.ChartJs.Doughnut2 = function(a, t, o, n, e, s) {
            if (u("#" + a).length) {
                var r = document.getElementById(a).getContext("2d"),
                    i = new Chart(r, {
                        type: "doughnut",
                        data: {
                            labels: t,
                            datasets: [{
                                label: "949",
                                lineTension: 0,
                                backgroundColor: o,
                                borderColor: e,
                                borderWidth: 3,
                                hoverBorderColor: e,
                                data: n
                            }]
                        },
                        options: {
                            legend: {
                                display: !1,
                                labels: {
                                    boxWidth: 10,
                                    fontColor: "#000"
                                }
                            },
                            rotation: -2,
                            cutoutPercentage: s,
                            responsive: !0,
                            maintainAspectRatio: !1,
                            tooltips: {
                                callbacks: {
                                    title: function(a, t) {
                                        return t.labels[a[0].index]
                                    },
                                    label: function(a, t) {
                                        return t.datasets[0].data[a.index] + " %"
                                    }
                                },
                                backgroundColor: "#eff6ff",
                                titleFontSize: 13,
                                titleFontColor: "#6783b8",
                                titleMarginBottom: 10,
                                bodyFontColor: "#9eaecf",
                                bodyFontSize: 14,
                                bodySpacing: 4,
                                yPadding: 15,
                                xPadding: 15,
                                footerMarginTop: 5,
                                displayColors: !1
                            },
                            hover: {
                                onHover: function(a, t) {
                                    if (t.length) {
                                        var o = t[0]._index + 1,
                                            n = t[0]._chart.canvas.id;
                                        u('[data-canvas="' + n + '"] li').removeClass("active"), u('[data-canvas="' + n + '"] li:nth-child(' + o + ")").addClass("active")
                                    } else u('[data-canvas="' + n + '"] li').removeClass("active")
                                }
                            }
                        }
                    });
                h.on("resize", function() {
                    i.resize()
                })
            }
        }, c.Chart.ChartJs.Pie = function(a, t, o, n, e, s, r, i) {
            if (u("#" + a).length) {
                var l = document.getElementById(a).getContext("2d"),
                    d = new Chart(l, {
                        type: "pie",
                        data: {
                            labels: t,
                            titles: o,
                            datasets: [{
                                label: "949",
                                lineTension: 0,
                                backgroundColor: n,
                                hoverBackgroundColor: e,
                                borderColor: r,
                                borderWidth: 2,
                                hoverBorderColor: r,
                                data: s,
                                animationDuration: 400
                            }]
                        },
                        options: {
                            legend: !1,
                            cutoutPercentage: 0,
                            responsive: !0,
                            maintainAspectRatio: !1,
                            tooltips: {
                                callbacks: {
                                    title: function(a, t) {
                                        return t.labels[a[0].index]
                                    },
                                    label: function(a, t) {
                                        return t.datasets[0].data[a.index] + " %"
                                    }
                                },
                                backgroundColor: "transparent",
                                titleFontSize: 11,
                                bodyFontColor: "#fff",
                                bodyFontSize: 14,
                                bodyFontStyle: "bold",
                                bodySpacing: 0,
                                yPadding: 0,
                                xPadding: 0,
                                yAlign: "center",
                                xAlign: "center",
                                footerMarginTop: 5,
                                displayColors: !1
                            },
                            hover: {
                                onHover: function(a, t) {
                                    if (t.length) {
                                        var o = t[0]._index + 1,
                                            n = t[0]._chart.canvas.id;
                                        u('[data-canvas="' + n + '"] li').removeClass("active"), u('[data-canvas="' + n + '"] li:nth-child(' + o + ")").addClass("active")
                                    } else u('[data-canvas="' + n + '"] li').removeClass("active")
                                }
                            }
                        }
                    });
                h.on("resize", function() {
                    d.resize()
                })
            }
        }, 0 < t.length && t.each(function() {
            var a = u(this).children("li"),
                t = u(this).data("canvas"),
                o = u(this).data("border-color") ? u(this).data("border-color") : "#fff",
                n = u(this).data("canvas-cutout") ? u(this).data("canvas-cutout") : "70",
                e = u(this).data("canvas-type");
            if (e = void 0 === e || "" === e ? "doughnut" : e, void 0 !== t && "" !== t) {
                var s = [],
                    r = [],
                    i = [];
                a.each(function() {
                    var a = u(this).data("title"),
                        t = u(this).data("color"),
                        o = u(this).data("amount");
                    s.push(a), r.push(t), i.push(o), u(this).html('<span class="chart-c" style="background-color: ' + t + '"></span><span class="chart-l">' + a + '</span><span class="chart-p">' + o + "%</span>")
                }), "doughnut" === e ? c.Chart.ChartJs.Doughnut(t, s, r, i, o, n) : "pie" === e ? c.Chart.ChartJs.Pie(t, s, r, i, o) : "linechart" === e && c.Chart.ChartJs.Doughnut(t, s, r, i, o)
            } else console.log("Unable to draw canvas: " + t)
        }), 0 < o.length && o.each(function() {
            var a = u(this).children("li"),
                t = u(this).data("canvas"),
                o = u(this).data("border-color") ? u(this).data("border-color") : "#fff",
                n = u(this).data("canvas-cutout") ? u(this).data("canvas-cutout") : "40",
                e = u(this).data("canvas-type");
            if (e = void 0 === e || "" === e ? "doughnut" : e, void 0 !== t && "" !== t) {
                var r = [],
                    i = [],
                    l = [],
                    d = [],
                    h = [];
                a.each(function() {
                    var a = u(this).data("label"),
                        t = u(this).data("title"),
                        o = u(this).data("subtitle"),
                        n = u(this).data("color"),
                        e = u(this).data("color-hover"),
                        s = u(this).data("amount");
                    r.push(a), i.push(t), l.push(n), d.push(e), h.push(s), u(this).html('<div class="chart-data-item"><span class="chart-label">' + t + '</span><span class="chart-info"><span class="chart-percent">' + s + '% </span><span class="chart-sublabel">' + o + "</span></span></div>")
                }), "doughnut" === e ? c.Chart.ChartJs.Doughnut(t, r, i, l, h, o, n) : "pie" === e ? c.Chart.ChartJs.Pie(t, r, i, l, d, h, o) : "linechart" === e && c.Chart.ChartJs.Doughnut(t, r, i, l, h, o)
            } else console.log("Unable to draw canvas: " + t)
        }), 0 < n.length && n.each(function() {
            var a = u(this).children("li"),
                t = u(this).data("canvas"),
                o = u(this).data("border-color") ? u(this).data("border-color") : "#122272",
                n = u(this).data("canvas-cutout") ? u(this).data("canvas-cutout") : "40",
                e = u(this).data("canvas-type");
            if (e = void 0 === e || "" === e ? "doughnut" : e, void 0 !== t && "" !== t) {
                var s = [],
                    r = [],
                    i = [],
                    l = [];
                a.each(function() {
                    var a = u(this).data("title"),
                        t = (u(this).data("subtitle"), u(this).data("color")),
                        o = u(this).data("color-hover"),
                        n = u(this).data("amount");
                    s.push(a), r.push(t), i.push(o), l.push(n), u(this).html('<span class="chart-l">' + a + '</span><span class="chart-p" style="background-color: ' + t + '" ><span>' + n + "%</span></span>")
                });
                for (var d = 0; d < a.length + 1; d++) a.eq(d - 1).addClass("chart-index-" + d);
                "doughnut" === e ? c.Chart.ChartJs.Doughnut2(t, s, r, l, o, n) : "pie" === e ? c.Chart.ChartJs.Pie(t, s, r, i, l, o) : "linechart" === e && c.Chart.ChartJs.Doughnut(t, s, r, l, o)
            } else console.log("Unable to draw canvas: " + t)
        })
    }, c.components.docReady.push(c.Chart.ChartJs), c
}(NioApp, jQuery, window);