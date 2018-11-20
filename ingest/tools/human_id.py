import math
import random 

##### ADJS
# SET1 - Base
adjs = [
    "autumn", "hidden", "bitter", "misty", "silent", "empty", "dry", "dark",
    "summer", "icy", "delicate", "quiet", "white", "cool", "spring", "winter",
    "patient", "twilight", "dawn", "crimson", "wispy", "weathered", "blue",
    "billowing", "broken", "cold", "damp", "falling", "frosty", "green",
    "long", "late", "lingering", "bold", "little", "morning", "muddy", "old",
    "red", "rough", "still", "small", "sparkling", "throbbing", "shy",
    "wandering", "withered", "wild", "black", "young", "holy", "solitary",
    "fragrant", "aged", "snowy", "proud", "floral", "restless", "divine",
    "polished", "ancient", "purple", "lively", "nameless", "wiggly", "yellow"
 ]
# SET2 - Colors
adjs += ["ablaze","ablazing","accented","achromatic","ashen","ashy","atomic","beaming","bi-color","blazing","bleached","bleak","blended","blotchy","bold","brash","bright","brilliant","burnt","checkered","chromatic","classic","clean","colored","colorful","colorless","complementing","contrasting","cool","coordinating","crisp","dappled","dark","dayglo","deep","delicate","digital","dim","dirty","matte","medium","mellow","milky","mingled","mixed","monochromatic","motley","mottled","muddy","multicolored","multihued","murky","natural","neutral","opalescent","opaque","pale","pastel","patchwork","patchy","patterned","perfect","picturesque","plain","primary","prismatic","psychedelic","pure","radiant","reflective","rich","royal","ruddy","rustic","satiny","saturated","secondary","shaded","dotted","drab","dreary","dull","dusty","earth","electric","eye-catching","faded","faint","festive","fiery","flashy","flattering","flecked","florescent","frosty","full-toned","glistening","glittering","glowing","harsh","hazy","hot","hued","icy","illuminated","incandescent","intense","interwoven","iridescent","kaleidoscopic","lambent","light","loud","luminous","lusterless","lustrous","majestic","shining","shiny","shocking","showy","smoky","soft","solid","somber","soothing","sooty","sparkling","speckled","stained","streaked","streaky","striking","strong neutral","subtle","sunny","swirling","tinged","tinted","tonal","toned","traditional","translucent","transparent","two-tone","undiluted","uneven","uniform","vibrant","vivid","wan","warm","washed-out","waxen","wild"]
adjs += ["red","orange","yellow","green","blue","purple","rainbow","tricolor","lime","goldenrod","violet","lavender","fuchsia","cerise","pink","black","brown","white","polka-dotted","grey","mauve","leal","chartreuse","scarlet","blonde","lvergreen","cerulean","cyan","dotted"];

#SET3 - Seasons
adjs += ["abundant","amber","autumnal","blustery","bountiful","breezy","bright","brilliant","brisk","brown","changing","chilly","cold","colder","colored","colorful","comfortable","harvested","hibernating","howling","inspirational","magnificent","moonlit","orange","overgrown","rainy","raked","red","relaxing","ripe","roaring","rust-colored","cozy","crackling","crisp","crunchy","deciduous","earthy","enchanting","enjoyable","fallen","fireside","flannel","foggy","foraging","fresh","frosty","gold","golden","gray","scary","seasonal","soggy","spectacular","spooky","turning","unpredictable","vibrant","visual","vivid","wilted","wilting","windy","wondrous","woodland","yellow","abloom","active","airy","alive","anew","awakening","barefoot","beautiful","blissful","blooming","blossoming","blue","breezy","bright","bucolic","budding","buzzing","changing","cheerful","cheery","chirping","clean","cloudless","colorful","crisp","light","lively","lovely","lush","magnificent","melting","new","newborn","outdoor","pastel","peaceful","playing","pleasant","pretty","pure","rainy","refreshing","rejeuventating","relaxing","renewing","romping","scampering","seasonal","singing","delightful","energetic","energized","enjoyable","fair","fecund","fertile","floral","flourishing","fluffy","fragrant","free","fresh","gentle","grassy","green","growing","happy","hatching","healthy","heavenly","incredible","inspiring","invigorating","soft","sparkling","spectacular","springtime","sprouting","stunning","sun-drenched","sun-filled","sun-kissed","sunlit","sunny","sweet","sweet-smelling","swimming","teeming","tender","thriving","unpredictable","verdant","vernal","vibrant","warm","warming"]
adjs += ["ablaze","abloom","active","alive","allergic","aquaholic","backyard","balmy","barefoot","beautiful","blazing","blistering","boiling","breezy","bright","burning","cheerful","clammy","clear","cloudless","magical","moist","muggy","natural","oppressive","outdoor","patriotic","perfect","poolside","refreshing","relaxing","ripe","roasting","scorching","seasonal","sensational","shaded","sizzling","starry","steamy","delightful","dreamy","easy","endless","fragrant","free","fresh","green","grilled","growing","happy","hazy","heavenly","hot","humid","lakeside","lazy","leisurely","light","lovely","stifling","sultry","summery","sun-baked","sun-drenched","sun-filled","sun-kissed","sunburnt","sunny","sweating","sweaty","sweet","sweltering","tan","tropical","unforgettable","verdant","warm","youthful","arctic","bare","barren","biting","bleak","blustery","bored","boring","chilling","chilly","clear","cloudy","cold","cozy","crackling","crisp","crunchy","crystalline","dark","dead","depressing","desolate","icy","indoor","insulated","intensifying","isolated","isolating","jingling","leafless","lonely","long","melting","misty","nippy","northern","numb","opaline","overcast","polar","powdery","rainy","relentless","sad","sedentary","drafty","dreary","drenched","enchanted","extreme","fireside","flannel","fleecy","fluffy","foggy","freezing","frigid","frostbitten","frosty","frozen","glacial","glistening","gray","gusty","harsh","hazy","heated","howling","hypothermic","shivering","slippery","slushy","snowbound","snowy","sparkling","spiced","thaw","toasted","toasting","toasty","unending","wet","white","windy","wintertime","wintery","wintry","woolen","zippy"]

##### NOUNS
# SET1 - Base
nouns = [
    "waterfall", "river", "breeze", "moon", "rain", "wind", "sea", "morning",
    "snow", "lake", "sunset", "pine", "shadow", "leaf", "dawn", "glitter",
    "forest", "hill", "cloud", "meadow", "sun", "glade", "bird", "brook",
    "butterfly", "bush", "dew", "dust", "field", "fire", "flower", "firefly",
    "feather", "grass", "haze", "mountain", "night", "pond", "darkness",
    "snowflake", "silence", "sound", "sky", "shape", "surf", "thunder",
    "violet", "water", "wildflower", "wave", "water", "resonance", "sun",
    "wood", "dream", "cherry", "tree", "fog", "frost", "voice", "paper",
    "frog", "smoke", "star"
]

#SET 2 - Animals
nouns += ["alligator","ant","bear","bee","bird","camel","cat","cheetah","chicken","chimpanzee","cow","crocodile","deer","dog","dolphin","duck","eagle","elephant","fish","fly","fox","frog","giraffe","goat","goldfish","hamster","hippopotamus","horse","kangaroo","kitten","lion","lobster","monkey","octopus","owl","panda","pig","puppy","rabbit","rat","scorpion","seal","shark","sheep","snail","snake","spider","squirrel","tiger","turtle","wolf","zebra"]
nouns += ["ape","baboon","badger","bat","bear","bird","bobcat","bulldog","bullfrog","cat","catfish","cheetah","chicken","chipmunk","cobra","cougar","cow","crab","deer","dingo","dodo","dog","dolphin","donkey","dragon","dragonfly","duck","eagle","earwig","eel","elephant","emu","falcon","fireant","firefox","fish","fly","fox","frog","gecko","goat","goose","grasshopper","horse","hound","husky","impala","insect","jellyfish","kangaroo","ladybug","liger","lion","lionfish","lizard","mayfly","mole","monkey","moose","moth","mouse","mule","newt","octopus","otter","owl","panda","panther","parrot","penguin","pig","puma","pug","quail","rabbit","rat","rattlesnake","robin","seahorse","sheep","shrimp","skunk","sloth","snail","snake","squid","starfish","stingray","swan","termite","tiger","treefrog","turkey","turtle","vampirebat","walrus","warthog","wasp","wolverine","wombat","yak","zebra"]

adjs = list(set(adjs))
nouns = list(set(nouns))


def generate_name(separator='-', maxnum=100):
    num = int(math.floor(random.random() * maxnum))
    adj = random.choice(adjs)
    noun = random.choice(nouns)
    return '{adj}{separator}{noun}{separator}{num}'.format(
         adj=adj,
         noun=noun,
         num=num,
         separator=separator
     )
