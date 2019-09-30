import discord
from discord.utils import find, get
import platform, asyncio, string, operator, random, textwrap
import os, re, aiohttp
import math
from redbot.core.bot import Red
from redbot.core import checks, commands, bank
from redbot.core.utils.chat_formatting import bold, box, pagify
import scipy
import scipy.misc
import scipy.cluster
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageOps, ImageFilter
import time
import unicodedata
import scipy
import pathlib
from io import BytesIO
from . import classes
from . import mechanics
from . import config
from .cardList import Ship

datapath = str(pathlib.Path(__file__).parent / "data") + "/"
datapath2 = str(pathlib.Path(__file__).parent / "data/bgs") + "/"

default_avatar_url = "http://i.imgur.com/XPDO9VH.jpg"
normal_frame_url = "https://i.imgur.com/8hyUlUe.png"
rare_frame_url = "https://i.imgur.com/dLS2gjI.png"
elite_frame_url = "https://i.imgur.com/47fNUtE.png"
super_frame_url = "https://i.imgur.com/606VXyb.png"
supersuper_frame_url = "https://i.imgur.com/wju6598.png"

Bay_1 = "https://azurlane.koumakan.jp/w/images/3/3a/MainDayBG.png"

class Waifer(commands.Cog):
    """Ship card creator"""

    def __init__(self, bot):
        self.bot = bot

    def unicode_text_cleanse(self, text):
        return unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode("ascii")

    def font_lookup(self, faction_font):
        faction_fonts = {"Bilibili": "Bilibili.ttf", "Eagle Union": "Eagle Union.ttf", "Eastern Radiance": "Eastern Radiance.ttf", "Iris Libre": "Iris Libre.ttf", "Ironblood": "Ironblood.ttf", "KizunaAI": "KizunaAI.ttf", "Neptunia": "Neptunia.ttf", "North Union": "North Union.ttf", "Royal Navy": "Royal Nav.ttf", "Sakura Empire": "Sakura Empire1.ttf", "Sardegna Empire": "Sardegna Empire.ttf",  "Sirens": "Sirens.ttf", "Universal": "Universal.ttf", "Utawarerumono": "Utawarerumono.ttf", "Vichya Dominion": "Vichya Dominion.ttf"}
        font = faction_fonts[faction_font]
        return font
        
    def font_size_lookup(self, font_size):
        fonts_size = {"Bilibili": 80, "Eagle Union": 84, "Eastern Radiance": 32, "Iris Libre": 80, "Ironblood": 88, "KizunaAI": 80, "Neptunia": 84, "North Union": 60, "Royal Navy": 90, "Sakura Empire": 44, "Sardegna Empire": 80,  "Sirens": 120, "Universal": 80, "Utawarerumono": 80, "Vichya Dominion": 76}
        font_size = fonts_size[font_size]
        return font_size

    def font_size_lookup2(self, font_size2):
        fonts_size2 = {"Bilibili": 58, "Eagle Union": 58, "Eastern Radiance": 32, "Iris Libre": 58, "Ironblood": 58, "KizunaAI": 58, "Neptunia": 66, "North Union": 58, "Royal Navy": 64, "Sakura Empire": 36, "Sardegna Empire": 58,  "Sirens": 76, "Universal": 58, "Utawarerumono": 58, "Vichya Dominion": 58}
        font_size2 = fonts_size2[font_size2]
        return font_size2

    def txt_color_lookup(self, txt_color):
        txt_colors = {"Bilibili": (204, 242, 255, 255), "Eagle Union": (0, 191, 255, 255), "Eastern Radiance": (235, 153, 255, 255), "Iris Libre": (255, 255, 102, 255), "Ironblood": (230, 0, 0, 255), "KizunaAI": (255, 102, 204, 255), "Neptunia": (153, 51, 255, 255), "North Union": (204, 204, 204, 255), "Royal Navy": (0, 89, 179, 255), "Sakura Empire": (255, 204, 230, 255), "Sardegna Empire": (0, 102, 0, 255), "Sirens": (102, 0, 0, 255), "Universal": (255, 204, 0, 255), "Utawarerumono": (205, 92, 92, 255), "Vichya Dominion": (156, 48, 48, 255)}
        txt_color = txt_colors[txt_color]
        return txt_color
        
    def rarity_color_lookup(self, rare_color):
        rarity_color = {"N": (138, 133, 133, 230), "R": (60, 164, 209, 230), "E": (153, 82, 189, 230), "SR": (255, 204, 0, 230), "UR": (210, 179, 220, 230), "PR": (255, 204, 0, 230), "DC": (210, 179, 220, 230)}
        rare_color = rarity_color[rare_color]
        return rare_color

    def frame_lookup(self, rare_frame):
        rarity_frame = {"N": "https://i.imgur.com/8hyUlUe.png", "R": "https://i.imgur.com/dLS2gjI.png", "E": "https://i.imgur.com/47fNUtE.png", "SR": "https://i.imgur.com/606VXyb.png", "UR": "https://i.imgur.com/wju6598.png", "PR": "https://i.imgur.com/606VXyb.png", "DC": "https://i.imgur.com/wju6598.png"}
        rare_frame = rarity_frame[rare_frame]
        return rare_frame

    async def draw_profile(self, ctx, card):
        faction_font = self.font_lookup(card.faction)
        faction_font_file = datapath + 'fonts/{}'.format(faction_font)
        font_size = self.font_size_lookup(card.faction)
        font_size2 = self.font_size_lookup2(card.faction)
        #font_name = ImageFont.truetype("{}", 15).format(faction_font)

        font_bold_file = datapath + 'fonts/Uni_Sans_Heavy.ttf'
        font_file = datapath + 'fonts/fontg.ttf'
        font_std_file = datapath + 'fonts/Bold.ttf'
        font_italic_file = datapath + 'fonts/BoldItalic.ttf'
        font_thin_file = datapath + 'fonts/Pro-Regular.ttf'
        font_unicode_file = datapath + "fonts/unicode.ttf"


        fact_font = ImageFont.truetype(faction_font_file, font_size)
        fact_font2 = ImageFont.truetype(faction_font_file, font_size2)
        name_u_fnt = ImageFont.truetype(font_unicode_file, 30)
        title_fnt = ImageFont.truetype(font_std_file, 20)
        title_u_fnt = ImageFont.truetype(font_unicode_file, 22)
        label_fnt = ImageFont.truetype(font_bold_file, 21)
        hash_fnt = ImageFont.truetype(font_bold_file, 18)
        exp_fnt = ImageFont.truetype(font_bold_file, 19)
        exp_small_fnt = ImageFont.truetype(font_bold_file, 16)
        desc_fnt = ImageFont.truetype(font_bold_file, 20)
        rep_fnt = ImageFont.truetype(font_italic_file, 50)
        rep_r_fnt = ImageFont.truetype(font_std_file, 40)
        quote_fnt = ImageFont.truetype(font_bold_file, 26)
        symbol_u_fnt = ImageFont.truetype(font_unicode_file, 32)

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), u"{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        # ship components
        rare = mechanics.rarity_lookup(card.rarity)
        rare_color = self.rarity_color_lookup(card.rarity)
        bg_url = card.skin
        profile_url = card.icon
        user = card.skinname
        display_name = card.skinname
        back_ground = card.skinname
        frame_url = self.frame_lookup(card.rarity) #TEST TO FIX LATER
        frame_size = (760, 1120) # Full card size
        bg_size = (758, 1118) # Resizes Ship gurl i.e (900, 1400) zooms in

        # COLORS
        faction_text = self.txt_color_lookup(card.faction)
        white_color = (220,220,220,255)
        light_color = (210,210,210,255)
        dark_color = (100,100,100,255)

        # create image objects
        background_image = Image # Background
        ship_image = Image # Shipgurl
        profile_image = Image # Chibbi
        frame_image = Image # Frame
        

        # Gets Background
        random_image = random.choice(os.listdir(datapath2))
        f = datapath2 + random_image
        background_image = Image.open(f).convert('RGBA')

        # Gets Shipgurl
        try:
            async with self.session.get(bg_url) as r:
                imagebg = await r.content.read()
            ship_image = Image.open(BytesIO(imagebg)).convert('RGBA')
        except:
            with open(datapath + 'ships/{}.png'.format(user), 'rb') as f:
                ship_image = Image.open(BytesIO(f.read())).convert('RGBA')

        # Gets Chibbi
        async with self.session.get(profile_url) as r:
            image = await r.content.read()
        profile_image = Image.open(BytesIO(image)).convert('RGBA')

        # Gets Frame
        async with self.session.get(frame_url) as r:
            image = await r.content.read()
        frame_image = Image.open(BytesIO(image)).convert('RGBA')

        # set canvas
        bg_color = (255,255,255,255)
        result = Image.new('RGBA', frame_size)
        process = Image.new('RGBA', frame_size)

        # draw
        draw = ImageDraw.Draw(process)

        # puts in background
        background_image = ImageOps.fit(background_image, bg_size, Image.ANTIALIAS, 1, (0.5, 0.5)) #Ship Gurl Fit...

        ship_image = ImageOps.fit(ship_image, bg_size, Image.ANTIALIAS, 1, (0.5, 0.5)) #Ship Gurl Fit...
        blended = Image.alpha_composite(background_image, ship_image)
        #result.paste(ship_image,(1,1))

        overlay = Image.new('RGBA', bg_size)
        draw = ImageDraw.Draw(overlay) # Create a context for drawing things on it.
        draw.rectangle(((0,830), (760, 1120)), fill=(0,0,0,110))
        draw.rectangle([(32,820), (729, 830)], fill=(0,0,0,190)) # Break line

        head_align = 55 #User Name height

        draw.text((self._center(63, 716, card.skinname , fact_font), head_align-2), card.skinname ,  font=fact_font, fill=faction_text) # Name
        
        tit_align = 820 #Title height
        tit_text = self.unicode_text_cleanse(card.faction)
        draw.text((60, 825), tit_text, font=fact_font2, fill=faction_text) # Faction

        rarity_text = card.id
        draw.text((146, 38), rarity_text, font=symbol_u_fnt, fill=light_color) # ID
        rep_text = "{}".format(card.rarity)
        draw.text((60, 765), rep_text, font=rep_fnt, fill=rare_color) 
        draw.text((64, 765), rep_text, font=rep_fnt, fill=rare_color)

        draw.text((60, 1030), card.desc,  font=desc_fnt, fill=light_color) # Description

        global_symbol = u"\U0001F30E"
        fine_adjust = 1
        quote_color = self._contrast(rare_color, dark_color, white_color)

        if card.quote == '': #User Information
            offset = 900
        else:
            offset = 900
        margin = 60
        for line in textwrap.wrap(card.quote, width=30):
            draw.text((margin, offset), line, font=quote_fnt, fill=white_color)
            offset += quote_fnt.getsize(line)[1] + 1.2

        img = Image.alpha_composite(blended, overlay)
        result.paste(img,(1,1))

        # Add Frame
        multiplier = 1
        frame_size_x = 760
        frame_size_y = 1120
        frame_left = 0
        frame_top = 0

        # Create mask
        mask = Image.new('L', (frame_size_x, frame_size_y), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.rectangle((0, 0) + (frame_size_x, frame_size_y), fill = 255, outline = 0)

        # Put Frame on pic picture
        total_gap = 0
        border = int(total_gap/1)
        output = ImageOps.fit(frame_image, (frame_size_x, frame_size_y), centering=(0.5, 0.5))
        output = output.resize((frame_size_x, frame_size_y), Image.ANTIALIAS)
        mask = mask.resize((frame_size_x, frame_size_y), Image.ANTIALIAS)
        frame_image = frame_image.resize((frame_size_x, frame_size_y), Image.ANTIALIAS)
        process.paste(frame_image, (frame_left, frame_top), mask)

        # draw Chibi
        chibi_size = 170, 170
        chibi_left = 525
        chibi_top = 860

        # Put Chibi in pic picture
        profile_image.thumbnail(chibi_size, Image.ANTIALIAS)
        if random.random() < 0.5:
            profile_image = ImageOps.mirror(profile_image)
        process.paste(profile_image, (chibi_left, chibi_top))

        #result = self._add_corners(result, 5)
        result = Image.alpha_composite(result, process)

        result.save(datapath + 'temp/ship_profile.png', 'PNG', quality=100)

        # remove images
        try:
            os.remove(datapath + 'temp/ship_temp_profile_bg.png')
        except:
            pass
        try:
            os.remove(datapath + 'temp/ship_temp_profile_profile.png')
        except:
            pass

    # returns color that contrasts better in background
    def _contrast(self, bg_color, color1, color2):
        color1_ratio = self._contrast_ratio(bg_color, color1)
        color2_ratio = self._contrast_ratio(bg_color, color2)
        if color1_ratio >= color2_ratio:
            return color1
        else:
            return color2

    def _luminance(self, color):
        # convert to greyscale
        luminance = float((0.2126*color[0]) + (0.7152*color[1]) + (0.0722*color[2]))
        return luminance

    def _contrast_ratio(self, bgcolor, foreground):
        f_lum = float(self._luminance(foreground)+0.05)
        bg_lum = float(self._luminance(bgcolor)+0.05)

        if bg_lum > f_lum:
            return bg_lum/f_lum
        else:
            return f_lum/bg_lum

    # finds the the pixel to center the text
    def _center(self, start, end, text, font):
        dist = end - start
        width = font.getsize(text)[0]
        start_pos = start + ((dist-width)/2)
        return int(start_pos)

