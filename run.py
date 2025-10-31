import tkinter as tk
from tkinter import ttk
import math
import random
import json
import os
from pathlib import Path

# Try to import pynput, but make it optional
try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except Exception as e:
    PYNPUT_AVAILABLE = False
    print(f"pynput import failed: {e}")


# ============================================================================
# MODEL - Stores application state
# ============================================================================
class FOVModel:
    """Stores the state of the FOV overlay application."""
    
    def __init__(self):
        self.fov_visible = False
        self.fov_radius = 50
        self.active_tab = "Visuals"
        self.mouse_x = 0
        self.mouse_y = 0
        self.fov_color = "#00D9FF"
        self.fov_thickness = 2
        
        # Dummy states for other features
        self.aimbot_enabled = False
        self.silent_aim = False
        self.jitter = False
        self.jitter_amount = 5
        self.box_esp = False
        self.distance_esp = False
        self.health_esp = False
        self.fly = False
        self.noclip = False
        
        # Jitter state
        self.left_trigger_held = False
        self.right_trigger_held = False
        self.jitter_active = False
        self.jitter_method = "Both Mouse Buttons"
        self.v_key_held = False
    
    def set_fov_visible(self, visible):
        self.fov_visible = visible
    
    def set_fov_radius(self, radius):
        self.fov_radius = radius
    
    def set_active_tab(self, tab_name):
        self.active_tab = tab_name
    
    def update_mouse_position(self, x, y):
        self.mouse_x = x
        self.mouse_y = y
    
    def set_fov_color(self, color):
        self.fov_color = color
    
    def set_jitter(self, enabled):
        self.jitter = enabled
        if not enabled:
            self.jitter_active = False
    
    def set_jitter_amount(self, amount):
        self.jitter_amount = amount
    
    def to_dict(self):
        """Convert model state to dictionary for saving."""
        return {
            'fov_visible': self.fov_visible,
            'fov_radius': self.fov_radius,
            'fov_color': self.fov_color,
            'fov_thickness': self.fov_thickness,
            'jitter': self.jitter,
            'jitter_amount': self.jitter_amount,
            'jitter_method': self.jitter_method,
            'aimbot_enabled': self.aimbot_enabled,
            'silent_aim': self.silent_aim,
            'box_esp': self.box_esp,
            'distance_esp': self.distance_esp,
            'health_esp': self.health_esp,
            'fly': self.fly,
            'noclip': self.noclip
        }
    
    def from_dict(self, data):
        """Load model state from dictionary."""
        self.fov_visible = data.get('fov_visible', False)
        self.fov_radius = data.get('fov_radius', 50)
        self.fov_color = data.get('fov_color', '#00D9FF')
        self.fov_thickness = data.get('fov_thickness', 2)
        self.jitter = data.get('jitter', False)
        self.jitter_amount = data.get('jitter_amount', 5)
        self.jitter_method = data.get('jitter_method', 'Both Mouse Buttons')
        self.aimbot_enabled = data.get('aimbot_enabled', False)
        self.silent_aim = data.get('silent_aim', False)
        self.box_esp = data.get('box_esp', False)
        self.distance_esp = data.get('distance_esp', False)
        self.health_esp = data.get('health_esp', False)
        self.fly = data.get('fly', False)
        self.noclip = data.get('noclip', False)


# ============================================================================
# CONFIG MANAGER - Handles saving/loading configs
# ============================================================================
class ConfigManager:
    """Manages configuration files in AppData/Local/Pulsion/configs/"""
    
    def __init__(self):
        # Get AppData Local path
        if os.name == 'nt':  # Windows
            appdata = os.getenv('LOCALAPPDATA')
        else:  # Mac/Linux
            appdata = os.path.expanduser('~/.local/share')
        
        self.config_dir = Path(appdata) / 'Pulsion' / 'configs'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        print(f"Config directory: {self.config_dir}")
    
    def save_config(self, name, config_data):
        """Save configuration to file."""
        try:
            config_path = self.config_dir / f"{name}.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"Config saved: {config_path}")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def load_config(self, name):
        """Load configuration from file."""
        try:
            config_path = self.config_dir / f"{name}.json"
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return None
    
    def list_configs(self):
        """List all available config files."""
        try:
            configs = [f.stem for f in self.config_dir.glob('*.json')]
            return sorted(configs)
        except Exception as e:
            print(f"Error listing configs: {e}")
            return []
    
    def delete_config(self, name):
        """Delete a configuration file."""
        try:
            config_path = self.config_dir / f"{name}.json"
            if config_path.exists():
                config_path.unlink()
                print(f"Config deleted: {config_path}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting config: {e}")
            return False


# ============================================================================
# CUSTOM SCROLLBAR WIDGET
# ============================================================================
class CustomScrollbar(tk.Canvas):
    """Custom styled scrollbar."""
    
    def __init__(self, parent, command=None, **kwargs):
        super().__init__(parent, width=8, highlightthickness=0, bg="#0a0a0a", **kwargs)
        self.command = command
        self.thumb_color = "#333333"
        self.thumb_hover_color = "#00D9FF"
        self.track_color = "#0a0a0a"
        
        self.thumb_pos = 0
        self.thumb_size = 0.3
        self.dragging = False
        self.drag_start_y = 0
        self.is_hovering = False
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self._draw()
    
    def _draw(self):
        self.delete("all")
        height = self.winfo_height()
        
        if height <= 1:
            return
        
        # Draw track
        self.create_rectangle(0, 0, 8, height, fill=self.track_color, outline="")
        
        # Draw thumb
        thumb_height = max(30, height * self.thumb_size)
        thumb_y = self.thumb_pos * (height - thumb_height)
        
        color = self.thumb_hover_color if self.is_hovering or self.dragging else self.thumb_color
        
        # Rounded thumb
        self.create_rectangle(2, thumb_y, 6, thumb_y + thumb_height, 
                            fill=color, outline="", tags="thumb")
    
    def _on_enter(self, event):
        self.is_hovering = True
        self._draw()
    
    def _on_leave(self, event):
        if not self.dragging:
            self.is_hovering = False
            self._draw()
    
    def _on_click(self, event):
        self.dragging = True
        self.drag_start_y = event.y
        height = self.winfo_height()
        thumb_height = max(30, height * self.thumb_size)
        thumb_y = self.thumb_pos * (height - thumb_height)
        
        if thumb_y <= event.y <= thumb_y + thumb_height:
            self.drag_start_y = event.y - thumb_y
        else:
            # Jump to click position
            self.thumb_pos = max(0, min(1, (event.y - thumb_height/2) / (height - thumb_height)))
            self._draw()
            if self.command:
                self.command("moveto", self.thumb_pos)
    
    def _on_drag(self, event):
        if self.dragging:
            height = self.winfo_height()
            thumb_height = max(30, height * self.thumb_size)
            new_y = event.y - self.drag_start_y
            self.thumb_pos = max(0, min(1, new_y / (height - thumb_height)))
            self._draw()
            if self.command:
                self.command("moveto", self.thumb_pos)
    
    def _on_release(self, event):
        self.dragging = False
        self._draw()
    
    def set(self, first, last):
        """Update scrollbar based on visible portion."""
        first = float(first)
        last = float(last)
        
        self.thumb_size = last - first
        self.thumb_pos = first / (1 - self.thumb_size) if self.thumb_size < 1 else 0
        
        self._draw()
    
    def update_display(self):
        """Force redraw."""
        self.after(10, self._draw)


# ============================================================================
# COLOR WHEEL WIDGET
# ============================================================================
class ColorWheel(tk.Canvas):
    """Color wheel picker widget."""
    
    def __init__(self, parent, size=100, on_color_change=None, **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=0, 
                        bg="#0a0a0a", **kwargs)
        self.size = size
        self.radius = size // 2 - 10
        self.center = size // 2
        self.on_color_change = on_color_change
        self.current_color = "#00D9FF"
        
        self._draw_wheel()
        self.bind("<Button-1>", self._on_click)
    
    def _draw_wheel(self):
        self.delete("all")
        
        # Draw color segments
        segments = 36
        for i in range(segments):
            angle1 = (i / segments) * 360
            angle2 = ((i + 1) / segments) * 360
            
            hue = i / segments
            color = self._hsv_to_hex(hue, 1.0, 1.0)
            
            self.create_arc(
                self.center - self.radius, self.center - self.radius,
                self.center + self.radius, self.center + self.radius,
                start=angle1, extent=angle2 - angle1,
                fill=color, outline=color
            )
        
        # Draw center circle
        inner_r = 12
        self.create_oval(
            self.center - inner_r, self.center - inner_r,
            self.center + inner_r, self.center + inner_r,
            fill=self.current_color, outline="#00D9FF", width=2
        )
    
    def _hsv_to_hex(self, h, s, v):
        """Convert HSV to hex color."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def _on_click(self, event):
        dx = event.x - self.center
        dy = event.y - self.center
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance <= self.radius and distance >= 12:
            angle = math.atan2(dy, dx)
            hue = (angle / (2 * math.pi)) % 1.0
            self.current_color = self._hsv_to_hex(hue, 1.0, 1.0)
            self._draw_wheel()
            
            if self.on_color_change:
                self.on_color_change(self.current_color)


# ============================================================================
# TOGGLE BUTTON WIDGET
# ============================================================================
class ToggleButton(tk.Canvas):
    """Custom toggle button widget with smooth animation."""
    
    def __init__(self, parent, on_toggle=None, **kwargs):
        super().__init__(parent, width=44, height=22, highlightthickness=0, **kwargs)
        self.active = False
        self.on_toggle = on_toggle
        self.animation_progress = 0
        self.animating = False
        
        self.bg_off = "#1a1a1a"
        self.bg_on = "#00D9FF"
        self.circle_color = "#ffffff"
        
        self.bind("<Button-1>", self._toggle)
        self._draw()
    
    def _draw(self):
        self.delete("all")
        
        # Interpolate colors
        if self.animating:
            progress = self.animation_progress
            bg_color = self._interpolate_color(self.bg_off, self.bg_on, progress if self.active else 1 - progress)
        else:
            bg_color = self.bg_on if self.active else self.bg_off
        
        # Rounded rectangle background
        self.create_oval(0, 0, 22, 22, fill=bg_color, outline="")
        self.create_oval(22, 0, 44, 22, fill=bg_color, outline="")
        self.create_rectangle(11, 0, 33, 22, fill=bg_color, outline="")
        
        # Circle position
        if self.animating:
            progress = self.animation_progress if self.active else 1 - self.animation_progress
            x_pos = 11 + (progress * 18)
        else:
            x_pos = 29 if self.active else 11
        
        self.create_oval(x_pos - 7, 4, x_pos + 7, 18, fill=self.circle_color, outline="")
    
    def _interpolate_color(self, color1, color2, progress):
        """Interpolate between two hex colors."""
        c1 = [int(color1[i:i+2], 16) for i in (1, 3, 5)]
        c2 = [int(color2[i:i+2], 16) for i in (1, 3, 5)]
        result = [int(c1[i] + (c2[i] - c1[i]) * progress) for i in range(3)]
        return f"#{result[0]:02x}{result[1]:02x}{result[2]:02x}"
    
    def _animate(self):
        if self.animating:
            self.animation_progress += 0.15
            if self.animation_progress >= 1:
                self.animation_progress = 1
                self.animating = False
            self._draw()
            if self.animating:
                self.after(16, self._animate)
    
    def _toggle(self, event=None):
        self.active = not self.active
        self.animation_progress = 0
        self.animating = True
        self._animate()
        
        if self.on_toggle:
            self.on_toggle(self.active)
    
    def set_state(self, active):
        self.active = active
        self.animating = False
        self.animation_progress = 1
        self._draw()


# ============================================================================
# SCROLLABLE FRAME WIDGET
# ============================================================================
class ScrollableFrame(tk.Frame):
    """A scrollable frame widget with custom scrollbar."""
    
    def __init__(self, parent, bg="#0a0a0a", **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        
        # Create canvas and custom scrollbar
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = CustomScrollbar(self, command=self._on_scrollbar)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)
        
        # Configure canvas scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self._on_frame_configure()
        )
        
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self._on_canvas_scroll)
        
        # Pack elements
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind canvas width to scrollable frame width
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Bind mouse wheel - improved version
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        
        self.mousewheel_bound = False
    
    def _bind_mousewheel(self, event):
        """Bind mousewheel when mouse enters."""
        if not self.mousewheel_bound:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            self.canvas.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel)
            self.mousewheel_bound = True
    
    def _unbind_mousewheel(self, event):
        """Unbind mousewheel when mouse leaves."""
        if self.mousewheel_bound:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
            self.mousewheel_bound = False
    
    def _on_canvas_configure(self, event):
        """Adjust the width of the scrollable frame to match canvas width."""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def _on_frame_configure(self):
        """Update scroll region when frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._update_scrollbar()
    
    def _on_canvas_scroll(self, first, last):
        """Handle canvas scroll events."""
        self.scrollbar.set(first, last)
    
    def _on_scrollbar(self, *args):
        """Handle scrollbar movement."""
        self.canvas.yview(*args)
    
    def _update_scrollbar(self):
        """Update scrollbar visibility and size."""
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            canvas_height = self.canvas.winfo_height()
            content_height = bbox[3] - bbox[1]
            if content_height > canvas_height:
                visible_ratio = canvas_height / content_height
                self.scrollbar.thumb_size = visible_ratio
            else:
                self.scrollbar.thumb_size = 1.0
            self.scrollbar.update_display()
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        # Check if content is scrollable
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        
        canvas_height = self.canvas.winfo_height()
        content_height = bbox[3] - bbox[1]
        
        if content_height <= canvas_height:
            return  # No need to scroll
        
        # Determine scroll direction and amount
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")


# ============================================================================
# VIEW - Handles all GUI rendering
# ============================================================================
class FOVView:
    """Handles all GUI rendering for the FOV overlay app."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Pulsion Toolz")
        self.root.geometry("850x600")
        
        # Colors - Clean aesthetic
        self.bg_dark = "#0a0a0a"
        self.bg_sidebar = "#0f0f0f"
        self.bg_content = "#0a0a0a"
        self.bg_card = "#121212"
        self.accent = "#00D9FF"
        self.accent_dim = "#0099BB"
        self.text_color = "#ffffff"
        self.text_dim = "#666666"
        
        self.visible = True
        self.animation_running = False
        
        # Setup window properties
        try:
            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
        except Exception as e:
            print(f"Window setup error: {e}")
        
        # Main background
        self.bg = tk.Frame(root, bg=self.bg_dark)
        self.bg.pack(fill=tk.BOTH, expand=True)
        
        # Title bar
        self.title_bar = tk.Frame(self.bg, bg=self.bg_dark, height=60)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        
        # Logo/Title
        logo_frame = tk.Frame(self.title_bar, bg=self.bg_dark)
        logo_frame.pack(side=tk.LEFT, padx=25, pady=15)
        
        tk.Label(logo_frame, text="⚡", bg=self.bg_dark, fg=self.accent, 
                font=("Arial", 24)).pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(logo_frame, text="PULSION TOOLZ", bg=self.bg_dark, 
                fg=self.text_color, font=("Arial", 13, "bold")).pack(side=tk.LEFT)
        
        # Window controls
        controls = tk.Frame(self.title_bar, bg=self.bg_dark)
        controls.pack(side=tk.RIGHT, padx=15)
        
        self.close_btn = tk.Button(controls, text="✕", bg=self.bg_dark, fg=self.text_dim, 
                             bd=0, font=("Arial", 18), padx=12,
                             activebackground="#1a1a1a", activeforeground="#ff4444",
                             cursor="hand2", command=self.quit_app)
        self.close_btn.pack(side=tk.RIGHT)
        
        # Main container
        main_container = tk.Frame(self.bg, bg=self.bg_dark)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        self.sidebar = tk.Frame(main_container, bg=self.bg_sidebar, width=200)
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)
        self.sidebar.pack_propagate(False)
        
        # Content area
        self.content_frame = tk.Frame(main_container, bg=self.bg_content)
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.tab_buttons = {}
        self.pages = {}
        
        # FOV Overlay
        self.fov_overlay = None
        self.fov_canvas = None
    
    def quit_app(self):
        """Callback for close button."""
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
    
    def create_sidebar_button(self, icon, name, command):
        btn_frame = tk.Frame(self.sidebar, bg=self.bg_sidebar)
        btn_frame.pack(fill=tk.X, pady=1)
        
        btn = tk.Button(btn_frame, text=f"{icon}  {name}", bg=self.bg_sidebar, fg=self.text_dim, 
                       bd=0, padx=25, pady=18, font=("Arial", 10), command=command,
                       activebackground="#1a1a1a", activeforeground=self.text_color,
                       anchor=tk.W, relief=tk.FLAT, cursor="hand2")
        btn.pack(fill=tk.BOTH, expand=True)
        
        # Bind hover animations
        def on_enter(e):
            if self.tab_buttons.get(name) and self.tab_buttons[name]['active']:
                return
            btn.config(bg="#151515")
        
        def on_leave(e):
            if self.tab_buttons.get(name) and self.tab_buttons[name]['active']:
                return
            btn.config(bg=self.bg_sidebar)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        self.tab_buttons[name] = {'button': btn, 'active': False}
        return btn
    
    def create_page(self, name):
        """Create a scrollable page."""
        page = ScrollableFrame(self.content_frame, bg=self.bg_content)
        self.pages[name] = page
        return page.scrollable_frame  # Return the inner frame for content
    
    def show_page(self, name):
        for page_name, page in self.pages.items():
            if page_name == name:
                page.pack(fill=tk.BOTH, expand=True, padx=35, pady=25)
            else:
                page.pack_forget()
    
    def highlight_tab(self, name):
        for tab_name, tab_data in self.tab_buttons.items():
            btn = tab_data['button']
            if tab_name == name:
                btn.config(bg="#1a1a1a", fg=self.accent, font=("Arial", 10, "bold"))
                tab_data['active'] = True
            else:
                btn.config(bg=self.bg_sidebar, fg=self.text_dim, font=("Arial", 10))
                tab_data['active'] = False
    
    def toggle_visibility(self):
        """Toggle window visibility with smooth animation."""
        if self.animation_running:
            return
        
        self.animation_running = True
        
        if self.visible:
            # Fade out
            self._animate_fade(1.0, 0.0, lambda: self.root.withdraw())
            self.visible = False
        else:
            # Fade in
            self.root.deiconify()
            self._animate_fade(0.0, 1.0, None)
            self.visible = True
    
    def _animate_fade(self, start_alpha, end_alpha, callback):
        """Animate window opacity."""
        steps = 10
        current_step = [0]
        
        def step():
            current_step[0] += 1
            progress = current_step[0] / steps
            alpha = start_alpha + (end_alpha - start_alpha) * progress
            
            try:
                self.root.attributes("-alpha", alpha)
            except:
                pass
            
            if current_step[0] < steps:
                self.root.after(20, step)
            else:
                self.animation_running = False
                if callback:
                    callback()
        
        step()
    
    def create_fov_overlay(self):
        try:
            self.fov_overlay = tk.Toplevel(self.root)
            self.fov_overlay.overrideredirect(True)
            self.fov_overlay.attributes("-topmost", True)
            self.fov_overlay.attributes("-transparentcolor", "black")
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.fov_overlay.geometry(f"{screen_width}x{screen_height}+0+0")
            
            self.fov_canvas = tk.Canvas(self.fov_overlay, bg="black", highlightthickness=0)
            self.fov_canvas.pack(fill=tk.BOTH, expand=True)
            
            self.fov_overlay.withdraw()
            
            self.root.after(200, self._make_clickthrough)
        except Exception as e:
            print(f"FOV overlay error: {e}")
    
    def _make_clickthrough(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.fov_overlay.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            style = style | 0x00080000 | 0x00000020
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
        except Exception as e:
            print(f"Clickthrough error: {e}")
    
    def show_fov_overlay(self):
        if self.fov_overlay:
            self.fov_overlay.deiconify()
            self.fov_overlay.attributes("-topmost", True)
    
    def hide_fov_overlay(self):
        if self.fov_overlay:
            self.fov_overlay.withdraw()
    
    def draw_fov_circle(self, x, y, radius, color, thickness=2):
        if not self.fov_canvas:
            return
        try:
            self.fov_canvas.delete("all")
            self.fov_canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                outline=color, width=thickness
            )
        except:
            pass
    
    def clear_fov_canvas(self):
        if self.fov_canvas:
            self.fov_canvas.delete("all")
    
    def bind_title_bar_drag(self, start_callback, drag_callback):
        self.title_bar.bind("<Button-1>", start_callback)
        self.title_bar.bind("<B1-Motion>", drag_callback)


# ============================================================================
# PRESENTER - Handles logic and coordinates Model and View
# ============================================================================
class FOVPresenter:
    """Handles all application logic and coordinates Model and View."""
    
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.mouse_track_job = None
        self.jitter_job = None
        self.last_x = 0
        self.last_y = 0
        
        # Config manager
        self.config_manager = ConfigManager()
        
        # Mouse controller for jitter (if pynput available)
        if PYNPUT_AVAILABLE:
            self.mouse_controller = mouse.Controller()
            print("Mouse controller initialized")
        else:
            self.mouse_controller = None
            print("pynput not available - jitter disabled")
        
        self._setup_ui()
        self._bind_events()
        if PYNPUT_AVAILABLE:
            self._setup_keyboard_listener()
    
    def _setup_keyboard_listener(self):
        """Setup keyboard listener for Insert key."""
        if not PYNPUT_AVAILABLE:
            return
        
        try:
            def on_press(key):
                try:
                    if key == keyboard.Key.insert:
                        self.view.toggle_visibility()
                    # Check for 'v' key
                    elif hasattr(key, 'char') and key.char == 'v':
                        self.model.v_key_held = True
                        self._update_jitter_activation()
                except:
                    pass
            
            def on_release(key):
                try:
                    # Check for 'v' key release
                    if hasattr(key, 'char') and key.char == 'v':
                        self.model.v_key_held = False
                        self._update_jitter_activation()
                except:
                    pass
            
            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
            print("Keyboard listener started")
            
            # Also listen for mouse buttons
            def on_click(x, y, button, pressed):
                if button == mouse.Button.left:
                    self.model.left_trigger_held = pressed
                elif button == mouse.Button.right:
                    self.model.right_trigger_held = pressed
                
                self._update_jitter_activation()
            
            mouse_listener = mouse.Listener(on_click=on_click)
            mouse_listener.start()
            print("Mouse listener started")
        except Exception as e:
            print(f"Error setting up keyboard listener: {e}")
    
    def _update_jitter_activation(self):
        """Update jitter activation based on current method."""
        if not self.model.jitter:
            self.model.jitter_active = False
            return
        
        method = self.model.jitter_method
        
        if method == "Both Mouse Buttons":
            self.model.jitter_active = self.model.left_trigger_held and self.model.right_trigger_held
        elif method == "Single Key (V)":
            self.model.jitter_active = self.model.v_key_held
        elif method == "Always On":
            self.model.jitter_active = True
        elif method == "Hold Left Click":
            self.model.jitter_active = self.model.left_trigger_held
    
    def _setup_ui(self):
        # Create sidebar buttons
        self.view.create_sidebar_button("🎯", "Aimbot", lambda: self.switch_tab("Aimbot"))
        self.view.create_sidebar_button("📦", "ESP", lambda: self.switch_tab("ESP"))
        self.view.create_sidebar_button("⚙", "Misc", lambda: self.switch_tab("Misc"))
        self.view.create_sidebar_button("💾", "Configs", lambda: self.switch_tab("Configs"))
        
        # Create pages
        self._create_aimbot_page()
        self._create_esp_page()
        self._create_misc_page()
        self._create_configs_page()
        
        self.switch_tab("Aimbot")
        
        # Create overlay after delay
        self.view.root.after(300, self.view.create_fov_overlay)
    
    def _create_card(self, parent, title):
        """Create a clean card container."""
        card = tk.Frame(parent, bg=self.view.bg_card)
        card.pack(fill=tk.X, pady=(0, 15))
        
        # Title
        title_frame = tk.Frame(card, bg=self.view.bg_card)
        title_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(title_frame, text=title, bg=self.view.bg_card, 
                fg=self.view.text_color, font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        
        # Content area
        content = tk.Frame(card, bg=self.view.bg_card)
        content.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        return content
    
    def _create_option_row(self, parent, label_text):
        """Create option row with label."""
        row = tk.Frame(parent, bg=self.view.bg_card)
        row.pack(fill=tk.X, pady=8)
        
        tk.Label(row, text=label_text, bg=self.view.bg_card, 
                fg=self.view.text_dim, font=("Arial", 9)).pack(side=tk.LEFT)
        
        return row
    
    def _create_aimbot_page(self):
        page = self.view.create_page("Aimbot")
        
        # Header
        header = tk.Frame(page, bg=self.view.bg_content)
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header, text="Aimbot", bg=self.view.bg_content, 
                fg=self.view.text_color, font=("Arial", 18, "bold")).pack(anchor=tk.W)
        
        # FOV Circle card
        fov_card = self._create_card(page, "FOV Circle Overlay")
        
        # Enable toggle with color wheel
        toggle_row = self._create_option_row(fov_card, "Enable FOV Overlay")
        
        right_side = tk.Frame(toggle_row, bg=self.view.bg_card)
        right_side.pack(side=tk.RIGHT)
        
        # Color wheel
        self.color_wheel = ColorWheel(right_side, size=70, on_color_change=self.change_fov_color)
        self.color_wheel.pack(side=tk.RIGHT, padx=(15, 0))
        
        # Toggle
        self.fov_toggle = ToggleButton(right_side, on_toggle=self.toggle_fov, bg=self.view.bg_card)
        self.fov_toggle.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Radius slider
        radius_row = self._create_option_row(fov_card, "Circle Radius")
        
        self.radius_value = tk.Label(radius_row, text=f"{self.model.fov_radius}px", 
                                     bg=self.view.bg_card, fg=self.view.accent, 
                                     font=("Arial", 9, "bold"))
        self.radius_value.pack(side=tk.RIGHT)
        
        slider_frame = tk.Frame(fov_card, bg=self.view.bg_card)
        slider_frame.pack(fill=tk.X, pady=(5, 0))
        
        slider = tk.Scale(slider_frame, from_=20, to=300, orient=tk.HORIZONTAL, 
                         bg=self.view.bg_card, fg=self.view.text_color, 
                         troughcolor=self.view.bg_dark, activebackground=self.view.accent,
                         command=self.update_fov_radius, 
                         highlightthickness=0, showvalue=False, bd=0)
        slider.set(self.model.fov_radius)
        slider.pack(fill=tk.X)
        
        # Aimbot card
        aim_card = self._create_card(page, "Aimbot Settings")
        
        # Enable aimbot
        aim_row = self._create_option_row(aim_card, "Enable Aimbot")
        ToggleButton(aim_row, bg=self.view.bg_card).pack(side=tk.RIGHT)
        
        # Silent aim
        silent_row = self._create_option_row(aim_card, "Silent Aim")
        ToggleButton(silent_row, bg=self.view.bg_card).pack(side=tk.RIGHT)
        
        # Jitter card
        jitter_card = self._create_card(page, "Jitter")
        
        # Enable jitter
        jitter_row = self._create_option_row(jitter_card, "Enable Jitter")
        self.jitter_toggle = ToggleButton(jitter_row, on_toggle=self.toggle_jitter, bg=self.view.bg_card)
        self.jitter_toggle.pack(side=tk.RIGHT)
        
        # Jitter method dropdown
        method_row = self._create_option_row(jitter_card, "Activation Method")
        
        method_options = ["Both Mouse Buttons", "Single Key (V)", "Always On", "Hold Left Click"]
        self.jitter_method_var = tk.StringVar(value=method_options[0])
        
        method_dropdown = tk.OptionMenu(method_row, self.jitter_method_var, *method_options, 
                                       command=self.change_jitter_method)
        method_dropdown.config(bg=self.view.bg_card, fg=self.view.text_color, 
                              activebackground=self.view.accent, activeforeground=self.view.text_color,
                              highlightthickness=0, bd=0, font=("Arial", 8))
        method_dropdown["menu"].config(bg=self.view.bg_card, fg=self.view.text_color, 
                                       activebackground=self.view.accent)
        method_dropdown.pack(side=tk.RIGHT)
        
        # Jitter amount
        jitter_amount_row = self._create_option_row(jitter_card, "Jitter Intensity")
        
        self.jitter_val = tk.Label(jitter_amount_row, text="5", bg=self.view.bg_card, 
                             fg=self.view.accent, font=("Arial", 9, "bold"))
        self.jitter_val.pack(side=tk.RIGHT)
        
        jitter_slider_frame = tk.Frame(jitter_card, bg=self.view.bg_card)
        jitter_slider_frame.pack(fill=tk.X, pady=(5, 0))
        
        jitter_slider = tk.Scale(jitter_slider_frame, from_=1, to=50, orient=tk.HORIZONTAL, 
                                bg=self.view.bg_card, fg=self.view.text_color, 
                                troughcolor=self.view.bg_dark, activebackground=self.view.accent,
                                highlightthickness=0, showvalue=False, bd=0,
                                command=self.update_jitter_amount)
        jitter_slider.set(5)
        jitter_slider.pack(fill=tk.X)
        
        # Jitter status indicator
        self.jitter_status = tk.Label(jitter_card, text="⚪ Waiting for trigger", 
                                     bg=self.view.bg_card, fg=self.view.text_dim, 
                                     font=("Arial", 8, "bold"))
        self.jitter_status.pack(anchor=tk.W, pady=(10, 0))
    
    def _create_esp_page(self):
        page = self.view.create_page("ESP")
        
        # Header
        header = tk.Frame(page, bg=self.view.bg_content)
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header, text="ESP", bg=self.view.bg_content, 
                fg=self.view.text_color, font=("Arial", 18, "bold")).pack(anchor=tk.W)
        
        # ESP card
        esp_card = self._create_card(page, "ESP Options")
        
        # Box ESP
        box_row = self._create_option_row(esp_card, "Box ESP")
        ToggleButton(box_row, bg=self.view.bg_card).pack(side=tk.RIGHT)
        
        # Distance
        dist_row = self._create_option_row(esp_card, "Distance")
        ToggleButton(dist_row, bg=self.view.bg_card).pack(side=tk.RIGHT)
        
        # Health
        health_row = self._create_option_row(esp_card, "Health")
        ToggleButton(health_row, bg=self.view.bg_card).pack(side=tk.RIGHT)
    
    def _create_misc_page(self):
        page = self.view.create_page("Misc")
        
        # Header
        header = tk.Frame(page, bg=self.view.bg_content)
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header, text="Misc", bg=self.view.bg_content, 
                fg=self.view.text_color, font=("Arial", 18, "bold")).pack(anchor=tk.W)
        
        # Movement card
        misc_card = self._create_card(page, "Movement")
        
        # Fly
        fly_row = self._create_option_row(misc_card, "Fly")
        ToggleButton(fly_row, bg=self.view.bg_card).pack(side=tk.RIGHT)
        
        # Noclip
        noclip_row = self._create_option_row(misc_card, "Noclip")
        ToggleButton(noclip_row, bg=self.view.bg_card).pack(side=tk.RIGHT)
        
        # Info card
        info_card = self._create_card(page, "Information")
        
        info_text = tk.Label(info_card, 
                            text="Most features are for demonstration only.\nFunctional: FOV Overlay, Jitter\n\nPress INSERT to hide/show this menu\n\nNote: pynput library must be installed for jitter to work.\nInstall with: pip install pynput",
                            bg=self.view.bg_card, fg=self.view.text_dim, 
                            font=("Arial", 9), justify=tk.LEFT)
        info_text.pack(pady=10, anchor=tk.W)
        
        # Jitter methods info card
        methods_card = self._create_card(page, "Jitter Activation Methods")
        
        methods_text = tk.Label(methods_card, 
                            text="• Both Mouse Buttons: Hold left + right click together\n"
                                 "• Single Key (V): Press and hold the V key\n"
                                 "• Always On: Jitter runs continuously when enabled\n"
                                 "• Hold Left Click: Hold left mouse button only\n\n"
                                 "Choose the method that works best for your needs!",
                            bg=self.view.bg_card, fg=self.view.text_dim, 
                            font=("Arial", 8), justify=tk.LEFT)
        methods_text.pack(pady=10, anchor=tk.W)
    
    def _create_configs_page(self):
        page = self.view.create_page("Configs")
        
        # Header
        header = tk.Frame(page, bg=self.view.bg_content)
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header, text="Configs", bg=self.view.bg_content, 
                fg=self.view.text_color, font=("Arial", 18, "bold")).pack(anchor=tk.W)
        
        # Save config card
        save_card = self._create_card(page, "Save Configuration")
        
        # Config name entry
        name_frame = tk.Frame(save_card, bg=self.view.bg_card)
        name_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(name_frame, text="Config Name:", bg=self.view.bg_card, 
                fg=self.view.text_dim, font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.config_name_entry = tk.Entry(name_frame, bg=self.view.bg_dark, fg=self.view.text_color,
                                         insertbackground=self.view.accent, bd=0, 
                                         font=("Arial", 9), relief=tk.FLAT)
        self.config_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, ipadx=5)
        self.config_name_entry.insert(0, "config1")
        
        # Save button
        save_btn_frame = tk.Frame(save_card, bg=self.view.bg_card)
        save_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_btn = tk.Button(save_btn_frame, text="💾 Save Config", bg=self.view.accent, 
                           fg="#ffffff", bd=0, font=("Arial", 9, "bold"), 
                           padx=20, pady=8, cursor="hand2", command=self.save_config,
                           activebackground=self.view.accent_dim)
        save_btn.pack(side=tk.LEFT)
        
        self.save_status = tk.Label(save_btn_frame, text="", bg=self.view.bg_card, 
                                   fg=self.view.text_dim, font=("Arial", 8))
        self.save_status.pack(side=tk.LEFT, padx=(15, 0))
        
        # Load config card
        load_card = self._create_card(page, "Load Configuration")
        
        # Config list frame
        list_frame = tk.Frame(load_card, bg=self.view.bg_card)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Listbox for configs
        self.config_listbox = tk.Listbox(list_frame, bg=self.view.bg_dark, fg=self.view.text_color,
                                        selectbackground=self.view.accent, selectforeground="#ffffff",
                                        bd=0, font=("Arial", 9), highlightthickness=0, height=6)
        self.config_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Buttons frame
        btn_frame = tk.Frame(load_card, bg=self.view.bg_card)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        load_btn = tk.Button(btn_frame, text="📂 Load", bg=self.view.accent, 
                           fg="#ffffff", bd=0, font=("Arial", 9, "bold"), 
                           padx=15, pady=6, cursor="hand2", command=self.load_config,
                           activebackground=self.view.accent_dim)
        load_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        refresh_btn = tk.Button(btn_frame, text="🔄 Refresh", bg=self.view.bg_dark, 
                              fg=self.view.text_color, bd=0, font=("Arial", 9), 
                              padx=15, pady=6, cursor="hand2", command=self.refresh_configs,
                              activebackground="#1a1a1a")
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_btn = tk.Button(btn_frame, text="🗑️ Delete", bg="#ff4444", 
                             fg="#ffffff", bd=0, font=("Arial", 9, "bold"), 
                             padx=15, pady=6, cursor="hand2", command=self.delete_config,
                             activebackground="#cc0000")
        delete_btn.pack(side=tk.LEFT)
        
        self.load_status = tk.Label(btn_frame, text="", bg=self.view.bg_card, 
                                   fg=self.view.text_dim, font=("Arial", 8))
        self.load_status.pack(side=tk.LEFT, padx=(15, 0))
        
        # Info card
        info_card = self._create_card(page, "Information")
        
        config_path = self.config_manager.config_dir
        info_text = tk.Label(info_card, 
                            text=f"Configs are saved to:\n{config_path}\n\n"
                                 "You can share config files with others by copying the .json files.",
                            bg=self.view.bg_card, fg=self.view.text_dim, 
                            font=("Arial", 8), justify=tk.LEFT)
        info_text.pack(pady=10, anchor=tk.W)
        
        # Initial refresh
        self.refresh_configs()
    
    def save_config(self):
        """Save current configuration."""
        name = self.config_name_entry.get().strip()
        if not name:
            self.save_status.config(text="⚠️ Enter a name", fg="#ff4444")
            return
        
        # Remove any file extension if user added it
        name = name.replace('.json', '')
        
        config_data = self.model.to_dict()
        success = self.config_manager.save_config(name, config_data)
        
        if success:
            self.save_status.config(text="✓ Saved successfully", fg="#00FF00")
            self.refresh_configs()
        else:
            self.save_status.config(text="✗ Save failed", fg="#ff4444")
        
        # Clear status after 3 seconds
        self.view.root.after(3000, lambda: self.save_status.config(text=""))
    
    def load_config(self):
        """Load selected configuration."""
        selection = self.config_listbox.curselection()
        if not selection:
            self.load_status.config(text="⚠️ Select a config", fg="#ff4444")
            return
        
        name = self.config_listbox.get(selection[0])
        config_data = self.config_manager.load_config(name)
        
        if config_data:
            self.model.from_dict(config_data)
            self.apply_config_to_ui()
            self.load_status.config(text="✓ Loaded successfully", fg="#00FF00")
        else:
            self.load_status.config(text="✗ Load failed", fg="#ff4444")
        
        # Clear status after 3 seconds
        self.view.root.after(3000, lambda: self.load_status.config(text=""))
    
    def delete_config(self):
        """Delete selected configuration."""
        selection = self.config_listbox.curselection()
        if not selection:
            self.load_status.config(text="⚠️ Select a config", fg="#ff4444")
            return
        
        name = self.config_listbox.get(selection[0])
        success = self.config_manager.delete_config(name)
        
        if success:
            self.load_status.config(text="✓ Deleted", fg="#00FF00")
            self.refresh_configs()
        else:
            self.load_status.config(text="✗ Delete failed", fg="#ff4444")
        
        # Clear status after 3 seconds
        self.view.root.after(3000, lambda: self.load_status.config(text=""))
    
    def refresh_configs(self):
        """Refresh the config list."""
        self.config_listbox.delete(0, tk.END)
        configs = self.config_manager.list_configs()
        for config in configs:
            self.config_listbox.insert(tk.END, config)
    
    def apply_config_to_ui(self):
        """Apply loaded config to UI elements."""
        # Update FOV toggle and settings
        self.fov_toggle.set_state(self.model.fov_visible)
        if self.model.fov_visible:
            self.view.show_fov_overlay()
        else:
            self.view.hide_fov_overlay()
        
        # Update jitter toggle
        self.jitter_toggle.set_state(self.model.jitter)
        self.jitter_val.config(text=str(self.model.jitter_amount))
        
        # Update radius display
        self.radius_value.config(text=f"{self.model.fov_radius}px")
        
        # Update jitter method dropdown
        if hasattr(self, 'jitter_method_var'):
            self.jitter_method_var.set(self.model.jitter_method)
        
        # Update color wheel
        self.color_wheel.current_color = self.model.fov_color
        self.color_wheel._draw_wheel()
    
    def _bind_events(self):
        self.view.bind_title_bar_drag(self.start_drag, self.on_drag)
        self.track_mouse_loop()
        self.jitter_loop()
        self.update_jitter_status()
    
    def switch_tab(self, tab_name):
        self.model.set_active_tab(tab_name)
        self.view.show_page(tab_name)
        self.view.highlight_tab(tab_name)
    
    def toggle_fov(self, active):
        self.model.set_fov_visible(active)
        
        if active:
            self.view.show_fov_overlay()
        else:
            self.view.hide_fov_overlay()
            self.view.clear_fov_canvas()
    
    def toggle_jitter(self, active):
        self.model.set_jitter(active)
        self._update_jitter_activation()
        print(f"Jitter toggled: {active}")
    
    def change_jitter_method(self, method):
        """Change jitter activation method."""
        self.model.jitter_method = method
        self._update_jitter_activation()
        print(f"Jitter method changed to: {method}")
    
    def update_jitter_amount(self, value):
        amount = int(float(value))
        self.model.set_jitter_amount(amount)
        self.jitter_val.config(text=str(amount))
    
    def update_fov_radius(self, value):
        radius = int(float(value))
        self.model.set_fov_radius(radius)
        self.radius_value.config(text=f"{radius}px")
    
    def change_fov_color(self, color):
        self.model.set_fov_color(color)
    
    def update_jitter_status(self):
        """Update jitter status indicator."""
        try:
            if hasattr(self, 'jitter_status'):
                if not self.model.jitter:
                    self.jitter_status.config(text="⚪ Jitter disabled", fg=self.view.text_dim)
                elif self.model.jitter_active:
                    self.jitter_status.config(text="🟢 JITTERING ACTIVE", fg="#00FF00")
                else:
                    # Show method-specific waiting message
                    method = self.model.jitter_method
                    if method == "Both Mouse Buttons":
                        msg = "🟡 Hold both mouse buttons"
                    elif method == "Single Key (V)":
                        msg = "🟡 Press and hold V key"
                    elif method == "Always On":
                        msg = "🟡 Starting..."
                    elif method == "Hold Left Click":
                        msg = "🟡 Hold left mouse button"
                    else:
                        msg = "🟡 Waiting for trigger"
                    
                    self.jitter_status.config(text=msg, fg="#FFAA00")
        except:
            pass
        
        self.view.root.after(100, self.update_jitter_status)
    
    def jitter_loop(self):
        """Handle jitter when activated."""
        try:
            if self.model.jitter and self.model.jitter_active:
                if self.mouse_controller:
                    # Get current mouse position
                    current_pos = self.mouse_controller.position
                    
                    # Random jitter from current position
                    jitter_amount = self.model.jitter_amount
                    offset_x = random.randint(-jitter_amount, jitter_amount)
                    offset_y = random.randint(-jitter_amount, jitter_amount)
                    
                    # Move mouse relative to current position
                    new_x = current_pos[0] + offset_x
                    new_y = current_pos[1] + offset_y
                    
                    self.mouse_controller.position = (new_x, new_y)
        except Exception as e:
            pass
        
        # Run at 60 FPS for smooth jitter
        self.jitter_job = self.view.root.after(16, self.jitter_loop)
    
    def track_mouse_loop(self):
        if self.model.fov_visible:
            try:
                x = self.view.root.winfo_pointerx()
                y = self.view.root.winfo_pointery()
                
                # Only update if mouse moved significantly (reduces lag)
                if abs(x - self.last_x) > 2 or abs(y - self.last_y) > 2:
                    self.last_x = x
                    self.last_y = y
                    self.model.update_mouse_position(x, y)
                    
                    self.view.draw_fov_circle(x, y, self.model.fov_radius, 
                                             self.model.fov_color, self.model.fov_thickness)
            except:
                pass
        
        # 60 FPS tracking
        self.mouse_track_job = self.view.root.after(16, self.track_mouse_loop)
    
    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def on_drag(self, event):
        x = self.view.root.winfo_x() + event.x - self.drag_start_x
        y = self.view.root.winfo_y() + event.y - self.drag_start_y
        self.view.root.geometry(f"+{x}+{y}")
    
    def close_app(self):
        """Clean up and close the application."""
        if self.mouse_track_job:
            self.view.root.after_cancel(self.mouse_track_job)
        if self.jitter_job:
            self.view.root.after_cancel(self.jitter_job)
        self.view.root.quit()
        self.view.root.destroy()
    
    def run(self):
        self.view.root.mainloop()


# ============================================================================
# MAIN
# ============================================================================
def main():
    try:
        print("Starting Pulsion Toolz...")
        root = tk.Tk()
        print("Tk initialized")
        
        model = FOVModel()
        print("Model created")
        
        view = FOVView(root)
        print("View created")
        
        presenter = FOVPresenter(model, view)
        print("Presenter created")
        
        if PYNPUT_AVAILABLE:
            print("\n✓ pynput available - all features enabled")
            print("  - Press INSERT to toggle menu visibility")
            print("  - Multiple jitter activation methods available")
        else:
            print("\n✗ pynput not available - jitter feature disabled")
            print("  Install with: pip install pynput")
        
        print("\nStarting mainloop...")
        presenter.run()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
