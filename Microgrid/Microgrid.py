import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

class AdvancedEconomicSim:
    def __init__(self):
        # Initial Parameters (Default Values)
        self.init_solar, self.init_wind, self.init_diesel = 50.0, 20.0, 10.0
        self.init_load, self.init_batt = 30.0, 100.0
        
        self.grid_active = True
        self.scheduler_active = False
        self.show_cost_data = False  

        self.grid_buy_price = 0.15
        self.grid_sell_price = 0.08

        # Create Figure
        self.fig, (self.ax_pwr, self.ax_soc) = plt.subplots(2, 1, figsize=(11, 10))
        plt.subplots_adjust(left=0.1, right=0.9, top=0.88, bottom=0.42, hspace=0.45)
        self.fig.canvas.manager.set_window_title('Microgrid Strategic Command')

        self.update_logic(self.init_solar, self.init_wind, self.init_diesel, self.init_load, self.init_batt)
        
        # Plots
        self.l_sol, = self.ax_pwr.plot(self.hours, self.solar, label='Solar', color='#FFD700', lw=2)
        self.l_load, = self.ax_pwr.plot(self.hours, self.load, label='House Load', color='#FF4500', ls='--')
        self.bar_grid = self.ax_pwr.bar(self.hours, self.grid_flow, alpha=0.3, color='#2ECC71', label='Grid Flow')
        
        self.l_soc, = self.ax_soc.plot(self.hours, self.soc_history, color='#3498DB', lw=3, label='Battery SOC %')
        self.f_soc = self.ax_soc.fill_between(self.hours, self.soc_history, color='#3498DB', alpha=0.15)
        
        self.cost_text = self.fig.text(0.5, 0.94, '', ha='center', fontsize=11, 
                                     fontweight='bold', color='blue',
                                     bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

        self.setup_styling()
        self.create_controls()
        self.refresh_display()

    def update_logic(self, s_mul, w_mul, d_mul, l_mul, b_cap):
        self.hours = np.arange(24)
        self.solar = s_mul * np.exp(-((self.hours - 12)**2) / (2 * 3**2))
        self.wind = w_mul * (0.6 + 0.4 * np.sin(self.hours / 4))
        self.load = l_mul * (1 + 0.8 * np.exp(-((self.hours - 9)**2)/2) + 1.2 * np.exp(-((self.hours - 19)**2)/4))

        soc = b_cap * 0.5
        self.soc_history, self.grid_flow = [], []
        self.total_cost = 0.0

        for h in range(24):
            gen = self.solar[h] + self.wind[h] + d_mul
            net = gen - self.load[h]
            
            if self.scheduler_active and (10 <= h <= 14):
                charge_power = min(25.0, b_cap - soc)
                soc += charge_power
                flow = charge_power - net if self.grid_active else 0
            else:
                if net > 0:
                    charge = min(net, b_cap - soc, 20.0)
                    soc += charge
                    flow = -(net - charge) if self.grid_active else 0
                else:
                    needed = abs(net)
                    disch = min(needed, soc, 20.0)
                    soc -= disch
                    flow = (needed - disch) if self.grid_active else 0
                
            self.grid_flow.append(flow)
            self.soc_history.append((soc / b_cap) * 100)
            
            if flow > 0:
                self.total_cost += flow * self.grid_buy_price
            else:
                self.total_cost += flow * self.grid_sell_price

    def setup_styling(self):
        self.ax_pwr.set_title("POWER FLOW ANALYSIS", fontweight='bold', pad=15)
        self.ax_pwr.set_ylabel("kW")
        self.ax_pwr.legend(loc='upper right', ncol=2, fontsize='8')
        self.ax_soc.set_title("BATTERY STORAGE (STATE OF CHARGE)", fontweight='bold', pad=15)
        self.ax_soc.set_ylabel("%")
        self.ax_soc.set_ylim(0, 105)

    def create_controls(self):
        # Action Buttons Row 1
        self.ax_storm = self.fig.add_axes([0.05, 0.35, 0.15, 0.04])
        self.ax_clear = self.fig.add_axes([0.22, 0.35, 0.15, 0.04])
        self.ax_black = self.fig.add_axes([0.39, 0.35, 0.15, 0.04])
        self.ax_sched = self.fig.add_axes([0.56, 0.35, 0.18, 0.04])
        self.ax_reset = self.fig.add_axes([0.76, 0.35, 0.18, 0.04]) # Reset Button
        
        # Row 2
        self.ax_cost_btn = self.fig.add_axes([0.4, 0.28, 0.2, 0.035])
        
        self.btn_storm = Button(self.ax_storm, '⛈ Storm', color='#DCDCDC')
        self.btn_clear = Button(self.ax_clear, '☀ Clear', color='#FFFACD')
        self.btn_black = Button(self.ax_black, '🔌 Grid Toggle', color='#FFB6C1')
        self.btn_sched = Button(self.ax_sched, '🤖 Smart DES: OFF', color='#98FB98')
        self.btn_reset = Button(self.ax_reset, '🔄 Reset System', color='#FF6347', hovercolor='orange')
        self.btn_cost_toggle = Button(self.ax_cost_btn, '💰 Show/Hide Cost', color='#ADD8E6')

        self.btn_storm.on_clicked(self.set_storm)
        self.btn_clear.on_clicked(self.set_clear)
        self.btn_black.on_clicked(self.toggle_grid)
        self.btn_sched.on_clicked(self.toggle_scheduler)
        self.btn_reset.on_clicked(self.reset_defaults)
        self.btn_cost_toggle.on_clicked(self.toggle_cost_visibility)

        # Sliders
        self.ax_s_sol = self.fig.add_axes([0.15, 0.18, 0.25, 0.02])
        self.ax_s_wnd = self.fig.add_axes([0.15, 0.13, 0.25, 0.02])
        self.ax_s_dsl = self.fig.add_axes([0.15, 0.08, 0.25, 0.02])
        self.ax_s_lod = self.fig.add_axes([0.60, 0.18, 0.25, 0.02])
        self.ax_s_bat = self.fig.add_axes([0.60, 0.13, 0.25, 0.02])

        self.sld_sol = Slider(self.ax_s_sol, 'Solar ', 0, 100, valinit=self.init_solar, color='#FFD700')
        self.sld_wnd = Slider(self.ax_s_wnd, 'Wind ', 0, 100, valinit=self.init_wind, color='#00CED1')
        self.sld_dsl = Slider(self.ax_s_dsl, 'Diesel ', 0, 50, valinit=self.init_diesel, color='#A9A9A9')
        self.sld_lod = Slider(self.ax_s_lod, 'Load ', 10, 150, valinit=self.init_load, color='#FF4500')
        self.sld_bat = Slider(self.ax_s_bat, 'Battery ', 20, 500, valinit=self.init_batt, color='#3498DB')

        for s in [self.sld_sol, self.sld_wnd, self.sld_dsl, self.sld_lod, self.sld_bat]:
            s.on_changed(self.update_plot)

    def reset_defaults(self, event):
        # Reset Sliders
        self.sld_sol.reset()
        self.sld_wnd.reset()
        self.sld_dsl.reset()
        self.sld_lod.reset()
        self.sld_bat.reset()
        
        # Reset Toggles
        self.grid_active = True
        self.scheduler_active = False
        self.btn_sched.label.set_text('🤖 Smart DES: OFF')
        
        self.update_plot(None)

    def toggle_cost_visibility(self, event):
        self.show_cost_data = not self.show_cost_data
        self.refresh_display()
        self.fig.canvas.draw_idle()

    def toggle_scheduler(self, event):
        self.scheduler_active = not self.scheduler_active
        label = '🤖 Smart DES: ON' if self.scheduler_active else '🤖 Smart DES: OFF'
        self.btn_sched.label.set_text(label)
        self.update_plot(None)

    def set_storm(self, event):
        self.sld_sol.set_val(0.0); self.sld_wnd.set_val(100.0); self.sld_dsl.set_val(30.0)
        self.update_plot(None)

    def set_clear(self, event):
        self.sld_sol.set_val(50.0); self.sld_wnd.set_val(20.0); self.sld_dsl.set_val(10.0)
        self.update_plot(None)

    def toggle_grid(self, event):
        self.grid_active = not self.grid_active
        self.update_plot(None)

    def refresh_display(self):
        status = "GRID CONNECTED" if self.grid_active else "ISLANDED MODE"
        if self.show_cost_data:
            self.cost_text.set_text(f"Daily Operating Cost: ${self.total_cost:.2f} | Status: {status}")
        else:
            self.cost_text.set_text(f"System Status: {status}")

    def update_plot(self, val):
        self.update_logic(self.sld_sol.val, self.sld_wnd.val, self.sld_dsl.val, self.sld_lod.val, self.sld_bat.val)
        self.l_sol.set_ydata(self.solar)
        self.l_load.set_ydata(self.load)
        self.l_soc.set_ydata(self.soc_history)
        for rect, val_g in zip(self.bar_grid, self.grid_flow):
            rect.set_height(val_g)
        self.f_soc.remove()
        self.f_soc = self.ax_soc.fill_between(self.hours, self.soc_history, color='#3498DB', alpha=0.15)
        self.refresh_display()
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    app = AdvancedEconomicSim()
    plt.show()