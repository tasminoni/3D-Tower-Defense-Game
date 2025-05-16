from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# Camera variables
camera_radius = 350.0
camera_theta = math.radians(90)
camera_height = 350.0
fovY = 120
GRID_LENGTH = 600
GRID_CELL_SIZE = 100
ELEVATION = 5

GRID_SIZE = 10  
CELL_SIZE = GRID_LENGTH // GRID_SIZE  
BLACK_COLOR = (0.0, 0.0, 0.0)  
WHITE_COLOR = (1.0, 1.0, 1.0)  
TOWER_AREA_WHITE = (0.8, 0.8, 0.8) 
TOWER_AREA_BLACK = (0.2, 0.2, 0.2) 

TOWER_AREAS = [(2, 3), (4, 1), (6, 3), (8, 1)]

TOWER_TYPES = {
    "nafin": {
        "name": "Nafin Tower",
        "description": "Shoots single projectiles at a moderate rate",
        "ability": "single_shot",
        "range": 200,
        "fire_rate": 1.0,
        "damage": 10,
        "health": 100
    },
    "zephyr": {
        "name": "Zephyr Tower",
        "description": "Shoots single projectiles with a futuristic design",
        "ability": "single_shot",
        "range": 200,
        "fire_rate": 1.0,
        "damage": 10,
        "health": 200
    },
    "vortex": {
        "name": "Vortex Tower",
        "description": "Shoots single projectiles with a turbine-like structure",
        "ability": "single_shot",
        "range": 200,
        "fire_rate": 1.0,
        "damage": 10,
        "health": 300
    }
}

game_state = "selection"  
selected_tower_type = None
tower_position = (-250, 0, 0)  
tower_health = 100
game_score = 0
game_over = False
cheat_mode = False  
MAX_ENEMIES = 15
current_wave = 0
wave_active = False
enemies_spawned = 0
last_spawn_time = 0
spawn_interval = 1.5

arrow_angle = 0  
last_player_shot = 0
player_shot_cooldown = 0.2  
last_tower_shot = 0
#game_state = "selection" 
sound_on = True          
game_won = False 
camera_mode = "orbital"  
#fp_camera_height = 120  

upgrade_menu_active = False
additional_towers = []  

wave_notification = False
wave_notification_time = 0
wave_notification_duration = 3.0

wall_health = 20  
wall_max_health = 20  
wall_active = True  

# Wave definitions
class Wave:
    def __init__(self, enemy_count, health, speed, fire_rate, bullet_color):
        self.enemy_count = enemy_count
        self.health = health
        self.speed = speed
        self.fire_rate = fire_rate
        self.bullet_color = bullet_color 

WAVES = [
    Wave(enemy_count=3, health=10, speed=3.0, fire_rate=0.5, bullet_color=(1.0, 0.0, 0.0)), 
    Wave(enemy_count=8, health=10, speed=6.0, fire_rate=1.0, bullet_color=(0.0, 1.0, 0.0)),  
    Wave(enemy_count=13, health=10, speed=12.0, fire_rate=2.0, bullet_color=(0.0, 0.0, 1.0)), 
    Wave(enemy_count=18, health=10, speed=24.0, fire_rate=4.0, bullet_color=(0.0, 0.0, 0.0)),  
]

# Enemy class
class Enemy:
    def __init__(self, x, y, z, health, speed, fire_rate, bullet_color):
        self.x = x
        self.y = y
        self.z = z
        self.health = health
        self.base_speed = speed
        self.speed = speed
        self.last_shot = 0
        self.fire_rate = fire_rate
        self.range = 600
        self.damage = 0.5
        self.slowed = False
        self.slow_duration = 0
        self.bullet_color = bullet_color 

    def move_toward(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 5:
            speed = self.speed * 0.5 if self.slowed else self.speed
            self.x += (dx / distance) * speed * (1/60)
            self.y += (dy / distance) * speed * (1/60)

    def shoot(self, target_x, target_y):
        current_time = time.time()
        if current_time - self.last_shot >= 1/self.fire_rate:  
            distance = math.sqrt((target_x - self.x)**2 + (target_y - self.y)**2)
            if distance <= self.range:
                self.last_shot = current_time
                return True
        return False

# Projectile class
class Projectile:
    def __init__(self, x, y, z, target_x, target_y, speed, damage, source, color=None):
        self.x = x
        self.y = y
        self.z = z
        self.speed = speed
        self.damage = damage
        self.source = source  
        self.color = color   
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        self.vx = (dx / distance) * speed if distance != 0 else 0
        self.vy = (dy / distance) * speed if distance != 0 else 0

    def update(self):
        self.x += self.vx * (1/60)
        self.y += self.vy * (1/60)

enemies = []
projectiles = []

def spawn_enemy():
    global enemies_spawned, wave_active
    if current_wave >= len(WAVES):
        return
    wave = WAVES[current_wave]
    if enemies_spawned < wave.enemy_count:
        grid_min = -GRID_LENGTH / 2
        grid_max = GRID_LENGTH / 2
        x = grid_max
        y = random.uniform(grid_min, grid_max)
        if math.sqrt((x - tower_position[0])**2 + (y - tower_position[1])**2) > 200:

            enemies.append(Enemy(x, y, 0, wave.health, wave.speed, wave.fire_rate, wave.bullet_color))
            enemies_spawned += 1
    if enemies_spawned >= wave.enemy_count:
        wave_active = False


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    glColor3f(*color)  
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_grid():
    glPushMatrix()
    glTranslatef(-GRID_LENGTH / 2, -GRID_LENGTH / 2, ELEVATION)
    glBegin(GL_QUADS)
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if (i + j) % 2 == 0:
                glColor3f(*TOWER_AREA_WHITE if (i, j) in TOWER_AREAS else WHITE_COLOR)
            else:
                glColor3f(*TOWER_AREA_BLACK if (i, j) in TOWER_AREAS else BLACK_COLOR)
            x1 = i * CELL_SIZE
            y1 = j * CELL_SIZE
            x2 = (i + 1) * CELL_SIZE
            y2 = (j + 1) * CELL_SIZE
            glVertex3f(x1, y1, 0)
            glVertex3f(x2, y1, 0)
            glVertex3f(x2, y2, 0)
            glVertex3f(x1, y2, 0)
    glEnd()
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    for i in range(GRID_SIZE + 1):
        glVertex3f(i * CELL_SIZE, 0, 0)
        glVertex3f(i * CELL_SIZE, GRID_LENGTH, 0)
        glVertex3f(0, i * CELL_SIZE, 0)
        glVertex3f(GRID_LENGTH, i * CELL_SIZE, 0)
    glEnd()
    glPopMatrix()

def draw_walls():
    thickness = 5
    height = 50
    def wall(x1, y1, x2, y2, color):
        glColor3f(*color)
        glBegin(GL_QUADS)
        glVertex3f(x1, y1, 0)
        glVertex3f(x2, y2, 0)
        glVertex3f(x2, y2, height)
        glVertex3f(x1, y1, height)
        glEnd()
    glPushMatrix()
    glTranslatef(-GRID_LENGTH / 2, -GRID_LENGTH / 2, ELEVATION)
    wall(0, 0, thickness, GRID_LENGTH, (1, 1, 1))
    wall(GRID_LENGTH - thickness, 0, GRID_LENGTH, GRID_LENGTH, (0, 1, 1)) 
    wall(0, GRID_LENGTH - thickness, GRID_LENGTH, GRID_LENGTH, (0, 0, 1))  
    wall(0, 0, GRID_LENGTH, thickness, (0, 1, 0))  

    if wall_active:
        wall(100, 0, 100 + thickness, GRID_LENGTH, (1, 0, 0))  
    glPopMatrix()

def draw_tower():
    if not selected_tower_type:
        return
    glPushMatrix()
    glTranslatef(tower_position[0], tower_position[1], tower_position[2])
    
    if selected_tower_type == "nafin":

        glColor3f(0.8, 0.8, 0.8)  
        gluCylinder(gluNewQuadric(), 30, 30, 100, 8, 1)
        glTranslatef(0, 0, 100)
        glColor3f(0.8, 0.6, 0.2)  
        for i in range(8):
            glPushMatrix()
            glRotatef(i * 45, 0, 0, 1)
            glBegin(GL_QUADS)
            glVertex3f(30, 0, 0)
            glVertex3f(35, 0, 0)
            glVertex3f(35, 0, 20)
            glVertex3f(30, 0, 20)
            glEnd()
            glPopMatrix()
        glColor3f(0.8, 0.8, 0.8) 
        gluCylinder(gluNewQuadric(), 30, 30, 30, 8, 1)
        glTranslatef(0, 0, 30)
        glColor3f(0.6, 0.4, 0.2) 
        glBegin(GL_QUADS)
        glVertex3f(-10, -30, 0)
        glVertex3f(10, -30, 0)
        glVertex3f(10, -30, 20)
        glVertex3f(-10, -30, 20)
        glEnd()
        glColor3f(0, 0, 0)  
        glBegin(GL_QUADS)
        glVertex3f(-5, 20, 10)
        glVertex3f(5, 20, 10)
        glVertex3f(5, 20, 20)
        glVertex3f(-5, 20, 20)
        glEnd()
        glColor3f(1, 1, 1) 
        gluDisk(gluNewQuadric(), 0, 40, 8, 1)
        for i in range(8):
            glPushMatrix()
            glRotatef(i * 45, 0, 0, 1)
            glTranslatef(40, 0, 0)
            glBegin(GL_QUADS)
            glVertex3f(0, -5, 0)
            glVertex3f(0, 5, 0)
            glVertex3f(0, 5, 10)
            glVertex3f(0, -5, 10)
            glEnd()
            glPopMatrix()
        glColor3f(1, 0, 0)  
        glTranslatef(0, 0, 10)
        quadric = gluNewQuadric()
        gluCylinder(quadric, 40, 0, 30, 8, 1)

        glTranslatef(0, 0, 30)
        glRotatef(arrow_angle, 0, 0, 1)
        glColor3f(0.0, 1.0, 0.0)  
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0)
        glVertex3f(20, 5, 0)
        glVertex3f(20, -5, 0)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(20, 2, 0)
        glVertex3f(20, -2, 0)
        glVertex3f(40, -2, 0)
        glVertex3f(40, 2, 0)
        glEnd()
    
    elif selected_tower_type == "zephyr":
       
        glColor3f(0.2, 0.4, 0.8)  # Blue base
        gluCylinder(gluNewQuadric(), 30, 30, 100, 8, 1)
        glTranslatef(0, 0, 100)
        glColor3f(0.0, 0.8, 0.8)  # Cyan accents
        for i in range(8):
            glPushMatrix()
            glRotatef(i * 45, 0, 0, 1)
            glBegin(GL_QUADS)
            glVertex3f(30, 0, 0)
            glVertex3f(35, 0, 0)
            glVertex3f(35, 0, 20)
            glVertex3f(30, 0, 20)
            glEnd()
            glPopMatrix()
        glColor3f(0.2, 0.4, 0.8)  # Blue midsection
        gluCylinder(gluNewQuadric(), 30, 30, 30, 8, 1)
        glTranslatef(0, 0, 30)
        glColor3f(0.0, 0.8, 0.8)  # Cyan platform
        glBegin(GL_QUADS)
        glVertex3f(-10, -30, 0)
        glVertex3f(10, -30, 0)
        glVertex3f(10, -30, 20)
        glVertex3f(-10, -30, 20)
        glEnd()
        glColor3f(0.0, 0.0, 0.0)  
        glBegin(GL_QUADS)
        glVertex3f(-5, 20, 10)
        glVertex3f(5, 20, 10)
        glVertex3f(5, 20, 20)
        glVertex3f(-5, 20, 20)
        glEnd()
        glColor3f(1, 1, 1) 
        gluDisk(gluNewQuadric(), 0, 40, 8, 1)
  
        for i in range(12):
            glPushMatrix()
            glRotatef(i * 30, 0, 0, 1)
            glTranslatef(45, 0, 5)
            glColor3f(0.0, 0.8, 0.8)  
            gluSphere(gluNewQuadric(), 5, 8, 8)
            glPopMatrix()
        for i in range(8):
            glPushMatrix()
            glRotatef(i * 45, 0, 0, 1)
            glTranslatef(40, 0, 0)
            glBegin(GL_QUADS)
            glVertex3f(0, -5, 0)
            glVertex3f(0, 5, 0)
            glVertex3f(0, 5, 10)
            glVertex3f(0, -5, 10)
            glEnd()
            glPopMatrix()
        glColor3f(0.6, 0.2, 0.8)  
        glTranslatef(0, 0, 10)
        quadric = gluNewQuadric()
        gluCylinder(quadric, 40, 0, 30, 8, 1)
        # Draw arrow
        glTranslatef(0, 0, 30)
        glRotatef(arrow_angle, 0, 0, 1)
        glColor3f(1.0, 1.0, 1.0)  
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0)
        glVertex3f(20, 5, 0)
        glVertex3f(20, -5, 0)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(20, 2, 0)
        glVertex3f(20, -2, 0)
        glVertex3f(40, -2, 0)
        glVertex3f(40, 2, 0)
        glEnd()
    
    elif selected_tower_type == "vortex":
 
        glColor3f(0.2, 0.8, 0.2)  
        gluCylinder(gluNewQuadric(), 30, 30, 100, 8, 1)
        # Add vertical fins
        glColor3f(0.8, 0.8, 0.0)  
        for i in range(6):
            glPushMatrix()
            glRotatef(i * 60, 0, 0, 1)
            glTranslatef(30, 0, 50)
            glBegin(GL_QUADS)
            glVertex3f(0, -5, -20)
            glVertex3f(0, 5, -20)
            glVertex3f(0, 5, 20)
            glVertex3f(0, -5, 20)
            glEnd()
            glPopMatrix()
        glTranslatef(0, 0, 100)
        glColor3f(0.8, 0.8, 0.0)  
        for i in range(8):
            glPushMatrix()
            glRotatef(i * 45, 0, 0, 1)
            glBegin(GL_QUADS)
            glVertex3f(30, 0, 0)
            glVertex3f(35, 0, 0)
            glVertex3f(35, 0, 20)
            glVertex3f(30, 0, 20)
            glEnd()
            glPopMatrix()
        glColor3f(0.2, 0.8, 0.2)  
        gluCylinder(gluNewQuadric(), 30, 30, 30, 8, 1)
        glTranslatef(0, 0, 30)
        glColor3f(0.8, 0.8, 0.0)  
        glBegin(GL_QUADS)
        glVertex3f(-10, -30, 0)
        glVertex3f(10, -30, 0)
        glVertex3f(10, -30, 20)
        glVertex3f(-10, -30, 20)
        glEnd()
        glColor3f(0.0, 0.0, 0.0)  
        glBegin(GL_QUADS)
        glVertex3f(-5, 20, 10)
        glVertex3f(5, 20, 10)
        glVertex3f(5, 20, 20)
        glVertex3f(-5, 20, 20)
        glEnd()
        glColor3f(1, 1, 1)  # White disk
        gluDisk(gluNewQuadric(), 0, 40, 8, 1)
        for i in range(8):
            glPushMatrix()
            glRotatef(i * 45, 0, 0, 1)
            glTranslatef(40, 0, 0)
            glBegin(GL_QUADS)
            glVertex3f(0, -5, 0)
            glVertex3f(0, 5, 0)
            glVertex3f(0, 5, 10)
            glVertex3f(0, -5, 10)
            glEnd()
            glPopMatrix()
        glColor3f(1.0, 0.5, 0.0)  # Orange cone
        glTranslatef(0, 0, 10)
        quadric = gluNewQuadric()
        gluCylinder(quadric, 40, 0, 30, 8, 1)
        # Draw arrow
        glTranslatef(0, 0, 30)
        glRotatef(arrow_angle, 0, 0, 1)
        glColor3f(0.0, 0.0, 0.0)  # Black arrow
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0)
        glVertex3f(20, 5, 0)
        glVertex3f(20, -5, 0)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(20, 2, 0)
        glVertex3f(20, -2, 0)
        glVertex3f(40, -2, 0)
        glVertex3f(40, 2, 0)
        glEnd()
    
    glPopMatrix()

def draw_enemy(enemy):
    glPushMatrix()
    glTranslatef(enemy.x, enemy.y, enemy.z)

    glColor3f(0.5, 0.0, 0.5)  # Purple body
    quadric = gluNewQuadric()
    gluCylinder(quadric, 20, 10, 50, 8, 1)
    glTranslatef(0, 0, 50)
    gluCylinder(quadric, 25, 0, 30, 8, 1)
    glColor3f(0.6, 0.4, 0.2)  # Brown antenna
    glPushMatrix()
    glRotatef(45, 0, 1, 0)
    gluCylinder(quadric, 2, 2, 30, 8, 1)
    glTranslatef(0, 0, 30)
    glColor3f(1.0, 1.0, 0.0)  # Yellow tip
    gluSphere(quadric, 5, 8, 8)
    glPopMatrix()
    glPopMatrix()

def draw_projectile(projectile):
    glPushMatrix()
    glTranslatef(projectile.x, projectile.y, projectile.z + 20)
    if projectile.source == "enemy" or projectile.source == "enemy_to_wall":
   
        if projectile.color:
            glColor3f(*projectile.color)
        else:
            glColor3f(1.0, 0.0, 0.0)  
    else:
        glColor3f(1.0, 1.0, 0.0)  
    gluSphere(gluNewQuadric(), 8, 8, 8)
    glPopMatrix()

last_upgrade_score = 0


def update_game():
    global last_spawn_time, tower_health, last_tower_shot, game_score, game_over, game_won
    global current_wave, wave_active, enemies_spawned, wall_health, wall_active,max_towers_message,max_towers_message_time
    global upgrade_menu_active, arrow_angle,game_state, last_upgrade_score,max_level_message, max_level_message_time
    global insufficient_funds_message, insufficient_funds_message_time,wave_notification, wave_notification_time, wave_notification_duration

    if game_over:
        return

    current_time = time.time()
    if max_level_message and time.time() - max_level_message_time > 3.0:  # message for 3 seconds
        max_level_message = False

    if max_towers_message and time.time() - max_towers_message_time > 3.0:  # message for 3 seconds
        max_towers_message = False

    if insufficient_funds_message and time.time() - insufficient_funds_message_time > 3.0:
        insufficient_funds_message = False

    if wave_notification and current_time - wave_notification_time > wave_notification_duration:
        wave_notification = False



    if game_score >= 15 and not upgrade_menu_active and not game_over and not game_won:
        if game_score >= last_upgrade_score + 5:
            upgrade_menu_active = True
            game_state = "paused"  
            


    if not wave_active and not enemies and current_wave < len(WAVES):
        wave_active = True
        enemies_spawned = 0
        last_spawn_time = current_time

        if current_wave > 0:  
            wave_notification = True
            wave_notification_time = current_time
    
    
    if wave_active and current_time - last_spawn_time >= spawn_interval:
        spawn_enemy()
        last_spawn_time = current_time
    
    
    for enemy in enemies[:]:
       
        target_x = -200 + 5  # Wall x position
        if not wall_active:
            target_x = tower_position[0]  # Target tower if wall is destroyed
            
        target_y = tower_position[1]  # Always use tower's y position
        
        enemy.move_toward(target_x, target_y)
        
        # Check for wall collision
        if wall_active and enemy.x <= -200 + 15:
            # Enemy hit the wall
            wall_health -= 5  # Wall takes 5 damage on collision
            enemies.remove(enemy)
            
            # Check if wall is destroyed
            if wall_health <= 0:
                wall_active = False
                wall_health = 0
                print("Wall destroyed!")
            
            if wave_active and enemies_spawned < WAVES[current_wave].enemy_count:
                spawn_enemy()
                last_spawn_time = current_time
            continue
        
        # Enemy reaches tower (if wall is down)
        if not wall_active and enemy.x <= tower_position[0] + 30:
            enemies.remove(enemy)
            tower_health -= 10
            if tower_health <= 0:
                tower_health = 0
                game_over = True
            continue
        
        # Handle slow effect
        if enemy.slow_duration > 0:
            enemy.slow_duration -= 1/60
            if enemy.slow_duration <= 0:
                enemy.slowed = False
                enemy.speed = enemy.base_speed
        
        # Enemy shooting - determine target based on wall status
        distance_to_wall = abs(enemy.x - (-200 + 5))
        distance_to_tower = math.sqrt((tower_position[0] - enemy.x)**2 + (tower_position[1] - enemy.y)**2)
        
        # Enemy shooting at wall
        if wall_active and distance_to_wall <= enemy.range and enemy.shoot(-200 + 5, enemy.y):
            # Shoot at wall with enemy's bullet color
            projectiles.append(Projectile(
                enemy.x, enemy.y, enemy.z + 30, 
                -200 + 5, enemy.y, 
                100, enemy.damage, "enemy_to_wall", enemy.bullet_color
            ))
        elif not wall_active and distance_to_tower <= enemy.range and enemy.shoot(tower_position[0], tower_position[1]):
            # Shoot at tower with enemy's bullet color
            projectiles.append(Projectile(
                enemy.x, enemy.y, enemy.z + 30, 
                tower_position[0], tower_position[1], 
                100, enemy.damage, "enemy", enemy.bullet_color
            ))
    

    if cheat_mode and selected_tower_type and enemies:
        tower = TOWER_TYPES[selected_tower_type]

        cheat_fire_rate = tower["fire_rate"] * 1
        
        if current_time - last_tower_shot >= 1/cheat_fire_rate:

            cheat_range = GRID_LENGTH 
            
        
            closest_enemy = None
            min_distance = float('inf')
            
            for enemy in enemies:
                distance = math.sqrt((enemy.x - tower_position[0])**2 + (enemy.y - tower_position[1])**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_enemy = enemy
            
    
            if closest_enemy:
                last_tower_shot = current_time
         
                projectiles.append(Projectile(
                    tower_position[0], tower_position[1], 60, 
                    closest_enemy.x, closest_enemy.y, 
                    200, tower["damage"] * 10, "tower" 
                ))
           
                arrow_angle = math.degrees(math.atan2(closest_enemy.y - tower_position[1], closest_enemy.x - tower_position[0]))
    

    for tower in additional_towers:
        if enemies:
            tower_fire_rate = TOWER_TYPES["nafin"]["fire_rate"]*1  
            
            if current_time - tower["last_shot"] >= 1/tower_fire_rate:
              
                closest_enemy = None
                min_distance = float('inf')
                tower_range = TOWER_TYPES["nafin"]["range"]* 3
                
                for enemy in enemies:
                    distance = math.sqrt((enemy.x - tower["position"][0])**2 + 
                                        (enemy.y - tower["position"][1])**2)
                    if distance < min_distance: 
                        min_distance = distance
                        closest_enemy = enemy
                

                if closest_enemy and min_distance <= tower_range:
                    tower["last_shot"] = current_time
                    

                    
                    projectiles.append(Projectile(
                        tower["position"][0], tower["position"][1], tower["position"][2] + 60, 
                        closest_enemy.x, closest_enemy.y, 
                        200, TOWER_TYPES["nafin"]["damage"]*10, "tower"  # Faster projectiles
                    ))
                    print(f"Additional tower shooting at enemy at ({closest_enemy.x}, {closest_enemy.y})")
        
    # Update projectiles
    for proj in projectiles[:]:
        proj.update()
        
        # Handle projectile hitting the wall
        if wall_active and proj.source == "enemy_to_wall":
            if abs(proj.x - (-200 + 5)) < 10:
                wall_health -= 1  
                projectiles.remove(proj)
                
            
                if wall_health <= 0:
                    wall_active = False
                    wall_health = 0
                continue
        
        
        if proj.source == "tower":
            for enemy in enemies[:]:
                distance = math.sqrt((proj.x - enemy.x)**2 + (proj.y - enemy.y)**2)
                if distance < 15:  
                    if cheat_mode:
                     
                        enemy.health -= proj.damage
                        if enemy.health <= 0:
                            enemies.remove(enemy)
                            game_score += 1
                    else:
                        
                        enemies.remove(enemy)
                        game_score += 1
                    
                    # Remove the projectile after hit
                    if proj in projectiles:  # Check if proj still exists
                        projectiles.remove(proj)
                    break
        
        # Player projectiles
        elif proj.source == "player" and not cheat_mode:
            for enemy in enemies[:]:
                distance = math.sqrt((proj.x - enemy.x)**2 + (proj.y - enemy.y)**2)
                if distance < 15:
                    enemies.remove(enemy)
                    game_score += 1
                    projectiles.remove(proj)
                    break
        
        # Enemy projectiles to tower
        elif proj.source == "enemy":
            distance = math.sqrt((proj.x - tower_position[0])**2 + (proj.y - tower_position[1])**2)
            if distance < 30:
                tower_health -= 1
                print(f"Tower hit! Health: {tower_health}")
                projectiles.remove(proj)
                if tower_health <= 0:
                    tower_health = 0
                    game_over = True
            
        # Remove projectiles outside grid
        grid_min = -GRID_LENGTH / 2
        grid_max = GRID_LENGTH / 2
        if proj in projectiles and not (grid_min <= proj.x <= grid_max and grid_min <= proj.y <= grid_max):
            projectiles.remove(proj)
    
    
    if not enemies and not wave_active:
        if current_wave < len(WAVES) - 1:
            current_wave += 1
        elif current_wave == len(WAVES) - 1:
         
            game_won = True
            game_over = True 


def keyboardListener(key, x, y):
    global game_state, selected_tower_type, game_over, game_won, tower_health, game_score, enemies, projectiles
    global current_wave, wave_active, enemies_spawned, arrow_angle, cheat_mode, camera_mode
    global wall_health, wall_active, upgrade_menu_active, additional_towers,tower_position
    
    if key == b'\x1b': 
        if game_state == "playing":
            game_state = "paused"
        elif game_state == "paused":
            game_state = "playing"
            if upgrade_menu_active:
                upgrade_menu_active = False
        elif game_over or game_won:
          
            tower_health = 100
            game_score = 0
            enemies.clear()
            projectiles.clear()
            game_over = False
            game_won = False  
            game_state = "selection"
            selected_tower_type = None
            tower_position = (-250, 0, 0)
            current_wave = 0
            wave_active = False
            enemies_spawned = 0
            cheat_mode = False
            camera_mode = "orbital"
            
            wall_health = wall_max_health
            wall_active = True
            
            additional_towers = []
            upgrade_menu_active = False
        return

    if game_state == "selection":
        if key == b'1':
            selected_tower_type = "nafin"
            tower_health = TOWER_TYPES["nafin"]["health"]
            game_state = "playing"
        elif key == b'2':
            selected_tower_type = "zephyr"
            tower_health = TOWER_TYPES["zephyr"]["health"]
            game_state = "playing"
        elif key == b'3':
            selected_tower_type = "vortex"
            tower_health = TOWER_TYPES["vortex"]["health"]
            game_state = "playing"
    elif game_state == "playing":
        if key == b'a' or key == b'A':
            arrow_angle += 5  
        elif key == b'd' or key == b'D':
            arrow_angle -= 5  
        elif key == b'c' or key == b'C':
            cheat_mode = not cheat_mode  
    elif (game_over or game_won) and key == b'r':
        tower_health = 100
        game_score = 0
        enemies = []
        projectiles = []
        game_over = False
        game_won = False  
        game_state = "selection"
        selected_tower_type = None
        tower_position = (-250, 0, 0)
        current_wave = 0
        wave_active = False
        enemies_spawned = 0
        cheat_mode = False
        camera_mode = "orbital"
       
        wall_health = wall_max_health
        wall_active = True
      
        additional_towers = []
        upgrade_menu_active = False
        glutPostRedisplay()

def specialKeyListener(key, x, y):
    global camera_theta, camera_height,game_state
    if game_state == "playing":
        if key == GLUT_KEY_LEFT:
            camera_theta += 0.1
        elif key == GLUT_KEY_RIGHT:
            camera_theta -= 0.1
        elif key == GLUT_KEY_UP:
            camera_height += 10
        elif key == GLUT_KEY_DOWN:
            camera_height -= 10
        camera_height = max(50, min(1000, camera_height))

max_level_message = False
max_level_message_time = 0

max_towers_message = False
max_towers_message_time = 0

insufficient_funds_message = False
insufficient_funds_message_time = 0

def mouseListener(button, state, x, y):
    global tower_position, last_player_shot, game_state, sound_on, max_level_message, max_level_message_time
    global tower_health, game_score, selected_tower_type, current_wave, wave_active,game_won
    global enemies_spawned, cheat_mode, game_over, camera_mode,last_upgrade_score,insufficient_funds_message, insufficient_funds_message_time
    global wall_health, wall_active, upgrade_menu_active, additional_towers,max_towers_message,max_towers_message_time 
    
    # Handle upgrade menu clicks
    if upgrade_menu_active and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        y_gl = 800 - y  # Convert y coordinate
        
        # Upgrade tower button
        if 300 <= x <= 700 and 450 <= y_gl <= 510:
          
            if game_score >= 15 and selected_tower_type != "vortex":
                game_score -= 10  # Deduct cost
                
                # Upgrade the main tower
                if selected_tower_type == "nafin":
                    selected_tower_type = "zephyr"
                    tower_health = TOWER_TYPES["zephyr"]["health"]
                elif selected_tower_type == "zephyr":
                    selected_tower_type = "vortex"
                    tower_health = TOWER_TYPES["vortex"]["health"]
                
                upgrade_menu_active = False
                game_state = "playing"
                return
            elif selected_tower_type == "vortex":
               
                max_level_message = True
                max_level_message_time = time.time()
                upgrade_menu_active = False
                last_upgrade_score = game_score
                game_state = "playing"
                return
        
      
        elif 300 <= x <= 700 and 350 <= y_gl <= 410:
          
            if game_score < 15:
               
                insufficient_funds_message = True
                insufficient_funds_message_time = time.time()
                upgrade_menu_active = False
                game_state = "playing"
                return
            elif game_score >= 15 and len(additional_towers) < 2:
                game_score -= 15  # Deduct cost
                
               
                if len(additional_towers) == 0:
                   
                    new_tower_pos = (-250, 200, 0)
                else:
                 
                    new_tower_pos = (-250, -200, 0)
                
                
                additional_towers.append({
                    "position": new_tower_pos,
                    "last_shot": time.time() -5.0
                })
                
                upgrade_menu_active = False
                game_state = "playing"
                return
            elif len(additional_towers) >= 2:
             
                max_towers_message = True
                max_towers_message_time = time.time()
                upgrade_menu_active = False
                last_upgrade_score = game_score
                game_state = "playing"
                return
        
        elif 300 <= x <= 700 and 250 <= y_gl <= 310:
            print("Resume Game button clicked") 
            upgrade_menu_active = False
            game_state = "playing"
            last_upgrade_score = game_score
            glutPostRedisplay() 
            return
            
    
    if game_state == "selection" and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        y_gl = 800 - y 
        
        for btn in tower_selection_buttons:
            if (btn['x'] <= x <= btn['x'] + btn['w'] and 
                btn['y'] <= y_gl <= btn['y'] + btn['h']):
                selected_tower_type = btn['tower_type']
                tower_health = TOWER_TYPES[btn['tower_type']]["health"]
                game_state = "playing"
                glutPostRedisplay()
                return
    
   
    if game_state == "paused" and not upgrade_menu_active and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        
        y_gl = 800 - y
        button_y = [600, 500, 400, 300]
        for i, by in enumerate(button_y):
            if 350 <= x <= 650 and by <= y_gl <= by + 60:
                if i == 0: 
                 
                    tower_health = 100
                    game_score = 0
                    enemies.clear()
                    projectiles.clear()
                    game_over = False
                    game_won = False
                    game_state = "selection"
                    selected_tower_type = None
                    tower_position = (-250, 0, 0)
                    current_wave = 0
                    wave_active = False
                    enemies_spawned = 0
                    cheat_mode = False
                    additional_towers = []
                    upgrade_menu_active = False
                
                    wall_health = wall_max_health
                    wall_active = True
                    glutPostRedisplay()
                elif i == 1:  
                    game_state = "playing"
                elif i == 2:  
                    sound_on = not sound_on
                elif i == 3:  
                    glutLeaveMainLoop()
        glutPostRedisplay()
        return

    
    if game_state == "playing" and selected_tower_type:
        if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
          
            camera_mode = "first_person" if camera_mode == "orbital" else "orbital"
        elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            current_time = time.time()
            if current_time - last_player_shot >= player_shot_cooldown:
                last_player_shot = current_time
              
                angle_rad = math.radians(arrow_angle)
                target_x = tower_position[0] + math.cos(angle_rad) * 1000
                target_y = tower_position[1] + math.sin(angle_rad) * 1000
                projectiles.append(Projectile(tower_position[0], tower_position[1], 10, target_x, target_y, 200, 1, "player"))
        glutPostRedisplay()

def draw_menu():
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    
    glDisable(GL_DEPTH_TEST)
    
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
   
    glColor4f(0, 0, 0, 0.7)  
    glBegin(GL_QUADS)
    glVertex2f(200, 100)
    glVertex2f(800, 100)
    glVertex2f(800, 700)
    glVertex2f(200, 700)
    glEnd()

  
    button_y = [600, 500, 400, 300]
    labels = ["New Game", "Resume", f"Sound: {'On' if sound_on else 'Off'}", "Quit"]
    
    for i, label in enumerate(labels):
       
        glColor3f(0.2, 0.8, 0.3)
        glBegin(GL_QUADS)
        glVertex2f(350, button_y[i])
        glVertex2f(650, button_y[i])
        glVertex2f(650, button_y[i] + 60)
        glVertex2f(350, button_y[i] + 60)
        glEnd()
        
       
        glColor3f(1.0, 1.0, 1.0)
        glRasterPos2f(400, button_y[i] + 20)
        for ch in label:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
   
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(420, 670)
    for ch in "SETTINGS":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_upgrade_menu():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    

    glColor4f(0, 0, 0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(200, 200)
    glVertex2f(800, 200)
    glVertex2f(800, 550)
    glVertex2f(200, 550)
    glEnd()


    button_y = [450, 350, 250] 
    labels = ["Upgrade Tower (Cost: 10)", "Build New Tower (Cost: 15)", "Resume Game"]
    
    for i, label in enumerate(labels):
        glColor3f(0.2, 0.8, 0.3)
        glBegin(GL_QUADS)
        glVertex2f(300, button_y[i])
        glVertex2f(700, button_y[i])
        glVertex2f(700, button_y[i] + 60)
        glVertex2f(300, button_y[i] + 60)
        glEnd()
        
        glColor3f(1.0, 1.0, 1.0)
        glRasterPos2f(350, button_y[i] + 30)
        for ch in label:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
 
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(380, 520)
    for ch in "UPGRADE OPTIONS":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
   
    if game_state == "selection":
        gluLookAt(0, 0, 200, 0, 0, 0, 0, 1, 0)
    elif camera_mode == "first_person":
       
        angle_rad = math.radians(arrow_angle)
        
     
        camera_x = tower_position[0] - 100 * math.cos(angle_rad)
        camera_y = tower_position[1] - 100 * math.sin(angle_rad)
        camera_z = tower_position[2] + 300 
        
 
        look_x = tower_position[0] + 300 * math.cos(angle_rad)
        look_y = tower_position[1] + 300 * math.sin(angle_rad)
        look_z = tower_position[2] + 100 
        
        gluLookAt(
            camera_x, camera_y, camera_z, 
            look_x, look_y, look_z,  
            0, 0, 1  
        )
    else:  
        x = camera_radius * math.cos(camera_theta)
        y = camera_radius * math.sin(camera_theta)
        gluLookAt(x, y, camera_height, 0, 0, 0, 0, 0, 1)

def idle():
    if game_state == "playing" and not upgrade_menu_active:
        update_game()
    glutPostRedisplay()


tower_selection_buttons = [
    {'text': '1. Tower Type 1', 'x': 50, 'y': 600, 'w':165, 'h': 40, 'tower_type': 'nafin'},
    {'text': '2. Tower Type 2', 'x': 50, 'y': 550, 'w': 165, 'h': 40, 'tower_type': 'zephyr'},
    {'text': '3. Tower Type 3', 'x': 50, 'y': 500, 'w': 165, 'h': 40, 'tower_type': 'vortex'}
]

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    glEnable(GL_DEPTH_TEST)
    setupCamera()
    
    if game_state == "selection":
       
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # Draw title
        glColor3f(1.0, 1.0, 1.0)
        draw_text(50, 700, "3D Tower Defense Game", GLUT_BITMAP_HELVETICA_18)
        draw_text(50, 650, "Select a Tower Type:", GLUT_BITMAP_HELVETICA_18)
        
        
        for button in tower_selection_buttons:
            
            if button['tower_type'] == 'nafin':
                glColor3f(0.8, 0.4, 0.4) 
            elif button['tower_type'] == 'zephyr':
                glColor3f(0.4, 0.6, 0.8) 
            else:
                glColor3f(0.4, 0.8, 0.4)  
                
           
            glBegin(GL_QUADS)
            glVertex2f(button['x'], button['y'])
            glVertex2f(button['x'] + button['w'], button['y'])
            glVertex2f(button['x'] + button['w'], button['y'] + button['h'])
            glVertex2f(button['x'], button['y'] + button['h'])
            glEnd()
            
            
            glColor3f(1.0, 1.0, 1.0)  
            draw_text(button['x'] + 10, button['y'] + 10, button['text'], GLUT_BITMAP_HELVETICA_18)
        
       
        glColor3f(1.0, 1.0, 1.0)
        draw_text(50, 450, "Click on a tower to select", GLUT_BITMAP_HELVETICA_18)
        
       
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
    else:
        draw_grid()
        draw_walls()
        draw_tower()
        
        
        for tower in additional_towers:
            glPushMatrix()
            glTranslatef(tower["position"][0], tower["position"][1], tower["position"][2])
            
            
            glColor3f(0.8, 0.8, 0.8)  
            gluCylinder(gluNewQuadric(), 30, 30, 100, 8, 1)
            glTranslatef(0, 0, 100)
            glColor3f(0.8, 0.6, 0.2)  
            for i in range(8):
                glPushMatrix()
                glRotatef(i * 45, 0, 0, 1)
                glBegin(GL_QUADS)
                glVertex3f(30, 0, 0)
                glVertex3f(35, 0, 0)
                glVertex3f(35, 0, 20)
                glVertex3f(30, 0, 20)
                glEnd()
                glPopMatrix()
            glColor3f(0.8, 0.8, 0.8)  
            gluCylinder(gluNewQuadric(), 30, 30, 30, 8, 1)
            glTranslatef(0, 0, 30)
            glColor3f(0.6, 0.4, 0.2) 
            glBegin(GL_QUADS)
            glVertex3f(-10, -30, 0)
            glVertex3f(10, -30, 0)
            glVertex3f(10, -30, 20)
            glVertex3f(-10, -30, 20)
            glEnd()
            glColor3f(0, 0, 0)  
            glBegin(GL_QUADS)
            glVertex3f(-5, 20, 10)
            glVertex3f(5, 20, 10)
            glVertex3f(5, 20, 20)
            glVertex3f(-5, 20, 20)
            glEnd()
            glColor3f(1, 1, 1)  
            gluDisk(gluNewQuadric(), 0, 40, 8, 1)
            for i in range(8):
                glPushMatrix()
                glRotatef(i * 45, 0, 0, 1)
                glTranslatef(40, 0, 0)
                glBegin(GL_QUADS)
                glVertex3f(0, -5, 0)
                glVertex3f(0, 5, 0)
                glVertex3f(0, 5, 10)
                glVertex3f(0, -5, 10)
                glEnd()
                glPopMatrix()
            glColor3f(1, 0, 0)  
            glTranslatef(0, 0, 10)
            quadric = gluNewQuadric()
            gluCylinder(quadric, 40, 0, 30, 8, 1)
            glPopMatrix()
            
        for enemy in enemies:
            draw_enemy(enemy)
        for proj in projectiles:
            draw_projectile(proj)
        draw_text(10, 770, "3D Tower Defense Game")
        if selected_tower_type:
            draw_text(10, 740, f"Selected Tower: {TOWER_TYPES[selected_tower_type]['name']}")
        else:
            draw_text(10, 740, f"Available Towers: {', '.join([TOWER_TYPES[t]['name'] for t in TOWER_TYPES])}")
        draw_text(10, 710, f"Tower Health: {tower_health}")
        draw_text(10, 680, f"Score: {game_score}")
        draw_text(10, 650, f"Wave: {current_wave + 1}/{len(WAVES)}")
        draw_text(10, 620, f"Enemies: {len(enemies)}")
        draw_text(10, 590, f"Camera: theta={int(math.degrees(camera_theta))} deg, height={int(camera_height)}")
        draw_text(10, 560, f"Cheat Mode: {'ON' if cheat_mode else 'OFF'} (Press C to toggle)")
        draw_text(10, 530, f"Camera Mode: {camera_mode.replace('_', ' ').upper()} (Right-click to toggle)")
        draw_text(10, 500, f"Additional Towers: {len(additional_towers)}")
        
       
        if wall_active:
            draw_text(10, 470, f"Wall Health: {wall_health}/{wall_max_health}", GLUT_BITMAP_HELVETICA_18)
        else:
            draw_text(10, 470, "Wall Destroyed!", GLUT_BITMAP_HELVETICA_18)
            
        if game_state == "playing" or game_state == "paused":
            if game_won:
                # Display victory message with green color
                draw_text(400, 500, "YOU WIN!", GLUT_BITMAP_TIMES_ROMAN_24, color=(0.0, 1.0, 0.0))
                draw_text(350, 450, f"Final Score: {game_score}", GLUT_BITMAP_TIMES_ROMAN_24, color=(0.0, 1.0, 0.0))
                draw_text(300, 400, "Press ESC to Start New Game", GLUT_BITMAP_HELVETICA_18, color=(0.0, 1.0, 0.0))
            elif game_over:
                # Keep game over message red
                draw_text(400, 500, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24, color=(1.0, 0.0, 0.0))
                draw_text(350, 450, f"Score: {game_score}", GLUT_BITMAP_TIMES_ROMAN_24, color=(1.0, 0.0, 0.0))
                draw_text(300, 400, "Press ESC to Start New Game", GLUT_BITMAP_HELVETICA_18, color=(1.0, 0.0, 0.0))
    

    if max_level_message:
       
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        
        glColor3f(1.0, 0.3, 0.3) 
        
        draw_text(500, 700, "Not possible to upgrade the tower any more!", GLUT_BITMAP_TIMES_ROMAN_24)
        
        glDisable(GL_BLEND)
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

    if max_towers_message:
       
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        
        glColor3f(1.0, 0.3, 0.3) 
        draw_text(270, 650, "No more towers can be built!", GLUT_BITMAP_TIMES_ROMAN_24)
        
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

    if insufficient_funds_message:
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        
        glColor3f(1.0, 0.3, 0.3)  
        draw_text(300, 600, "Cannot upgrade - insufficient funds!", GLUT_BITMAP_TIMES_ROMAN_24)
        
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        

    if wave_notification:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
      
        glColor3f(1.0, 0.8, 0.0)  
        message = f"WAVE {current_wave + 1} COMING!"
        draw_text(500,700, message, GLUT_BITMAP_TIMES_ROMAN_24)
        
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

    
    if game_state == "paused" and not upgrade_menu_active:
        draw_menu()
    
   
    if upgrade_menu_active:
        draw_upgrade_menu()
    
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D Tower Defense Game")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()