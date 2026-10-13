import os
PROFILE=os.environ.get('PV_CHARACTER_PROFILE') in ('white-sailor','paired-characters')
# The source mage is the supplied black-haired glasses character; casual is white-haired.
HAIR=[231,233,243] if PROFILE else [100,117,188]
SKIN=[255,226,208]
CUFF=[61,62,70] if PROFILE else [37,36,33]
COAT=[72,73,83] if PROFILE else [167,130,83]
SLEEVE=[249,249,253] if PROFILE else [239,230,210]
SKIRT=[169,190,232] if PROFILE else [43,51,76]
AUTHOR='Character edit + Codex' if PROFILE else 'StuG_III + GPT6Astra'
CREDIT_LINES=[] if PROFILE else ['MUSHOKU TENSEI: ROXY','VISUAL FAN EDIT','StuG_III + GPT6Astra']
