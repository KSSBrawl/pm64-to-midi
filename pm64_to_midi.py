import mido, sys, argparse
from enum import Enum
from typing import List, BinaryIO

#-----------------------------------------------------------

PITCH_STEP_COARSE	= 8192 / 24
PITCH_STEP_FINE		= PITCH_STEP_COARSE / 100

cmd_len_table = [
	2, 1, 1, 1, 4, 3, 2, 0,
	2, 1, 1, 1, 1, 1, 1, 2,
	3, 1, 1, 0, 2, 1, 3, 1,
	0, 0, 0, 0, 3, 3, 3, 3
]

class EventTypes( Enum ):
	NOTE_OFF	= 0
	NOTE_ON		= 1
	CC			= 2
	PROGRAM		= 3
	WHEEL		= 4
	TEMPO		= 5
	TEMPO_FADE	= 6
	SYSEX		= 7

#-----------------------------------------------------------

# Values are the MIDI key and patch number
drum_map = {
	# STANDARD 1
	 0: ( 36,  0 ), # Std.1 K1
	 1: ( 38,  0 ), # Std.1 S1
	 2: ( 40,  0 ), # Std.1 S2
	 3: ( 42,  0 ), # C.Hi-Hat
	 4: ( 44,  0 ), # P.Hi-Hat
	 5: ( 46,  0 ), # O.Hi-hat
	 6: ( 50,  0 ), # Hi.Tom 1
	 7: ( 48,  0 ), # Hi.Tom 2
	 8: ( 47,  0 ), # MidTom 1
	 9: ( 45,  0 ), # MidTom 2
	10: ( 43,  0 ), # LowTom 1
	11:	( 41,  0 ), # LowTom 2
	12: ( 49,  0 ), # CrshCym1
	13: ( 57,  0 ), # CrshCym2
	14: ( 61,  0 ), # LowBongo
	15: ( 60,  0 ), # Hi.Bongo
	16: ( 79,  0 ), # Op.Cuica
	17: ( 78,  0 ), # Mt.Cuica
	18: ( 54,  0 ), # Tambourn
	19: ( 81,  0 ), # Op.Trigl
	20: ( 80,  0 ), # Mt.Trigl
	21: ( 63,  0 ), # OH Conga
	22: ( 64,  0 ), # LowConga
	23: ( 62,  0 ), # MH Conga
	24: ( 65,  0 ), # Hi.Timbl
	25: ( 66,  0 ), # LowTimbl
	26: ( 74,  0 ), # L.Guiro
	27: ( 73,  0 ), # S.Guiro
	# ORCHESTRA
	28: ( 36, 48 ), # Con.BD 1
	29: ( 38, 48 ), # Con.SD
	# TR-808
	30: ( 35, 25 ), # 808 BD2
	31: ( 36, 25 ), # 808 BD
	32: ( 38, 25 ), # 808 S1
	33: ( 40, 25 ), # 808 S2
	34: ( 42, 25 ), # 808 CHH2
	35: ( 46, 25 ), # 808 OHH
	# STANDARD 1
	36: ( 51,  0 ), # RideCym1
	37: ( 53,  0 ), # RideBell
	# ROOM
	38: ( 36,  8 ), # Room K1
	39: ( 36,  8 ), # Room K2
	40: ( 38,  8 ), # Room S1
	# DANCE
	41: ( 35, 26 ), # 909 CmpK
	42: ( 36, 26 ), # Elec.K2
	43: ( 38, 26 ), # House SD
	# STANDARD 1
	44: ( 69,  0 ), # Cabasa
	# unknown
	45: ( 26,  0 ),
	# STANDARD 1
	46: ( 75,  0 ), # Claves
	47: ( 56,  0 ), # Cowbell
	48: ( 67,  0 ), # Hi.Agogo
	49: ( 68,  0 ), # LowAgogo
	50: ( 76,  0 ), # Hi.W.Blk
	51: ( 77,  0 ), # LowW.Blk
	52: ( 72,  0 ), # LL.Whisl
	53: ( 71,  0 ), # Sh.Whisl
	54: ( 82,  0 ), # Shaker
	55: ( 70,  0 ), # Maracas
	# ELECTRONIC
	56: ( 39, 24 ), # HandClap
	# STANDARD 1
	57: ( 39,  0 ), # 909 Clap
	58: ( 37,  0 ), # Sd.Stick
	59: ( 31,  0 ), # Sticks
	60: ( 58,  0 ), # Vib-slap
}

#-----------------------------------------------------------

drum_ex_map = {
	0x9a: ( 36, 30 ), # 909 K1
	0x9b: ( 38, 30 ), # 909 S2
	0x9c: ( 45, 30 ), # 909 Mid2
	0x9d: ( 38,  0 ), # Std.1 S1
	0x9e: ( 36, 41 ), # Jazz K1
	0x9f: ( 38, 41 ), # B.Tap 1

	0xb0: ( 36,  0 ), # Std.1 K1
	0xb1: ( 38,  0 ), # Std.1 S1
	0xb2: ( 40,  0 ), # Std.1 S2
	0xb3: ( 42,  0 ), # C.Hi-Hat
	0xb4: ( 44,  0 ), # P.Hi-Hat
	0xb5: ( 46,  0 ), # O.Hi-Hat
	0xb6: ( 49,  0 ), # CrshCym1
	0xb7: ( 57,  0 ), # CrshCym2
	0xb8: ( 50,  0 ), # Hi.Tom 1
	0xb9: ( 48,  0 ), # Hi.Tom 2
	0xba: ( 47,  0 ), # MidTom 1
	0xbb: ( 45,  0 ), # MidTom 2
	0xbc: ( 43,  0 ), # LowTom 1
	0xbd: ( 41,  0 ), # LowTom 2
	0xbe: ( 51,  0 ), # RideCym1
	0xbf: ( 53,  0 ), # RideBell
	0xc0: ( 36, 48 ), # Con.BD 1
	0xc1: ( 38, 48 ), # Con.SD
	0xc2: ( 59, 48 ), # Con.Cym1
	0xc3: ( 35, 26 ), # 909 CmpK
	0xc4: ( 36, 26 ), # Elec.K2
	0xc5: ( 38, 26 ), # House SD

	0xc7: ( 36,  8 ), # Room K1
	0xc8: ( 38,  8 ), # Room S1
	0xc9: ( 35, 25 ), # 808 BD2
	0xca: ( 36, 25 ), # 808 BD
	0xcb: ( 38, 25 ), # 808 S1
	0xcc: ( 40, 25 ), # 808 S1
	0xcd: ( 42, 25 ), # 808 CHH2
	0xce: ( 46, 25 ), # 808 OHH

	0xd0: ( 61,  0 ), # LowBongo
	0xd1: ( 60,  0 ), # Hi.Bongo
	0xd2: ( 79,  0 ), # Op.Cuica
	0xd3: ( 78,  0 ), # Mt.Cuica
	0xd4: ( 54,  0 ), # Tambourn
	0xd5: ( 81,  0 ), # Op.Trigl
	0xd6: ( 63,  0 ), # OH Conga
	0xd7: ( 64,  0 ), # LowConga
	0xd8: ( 62,  0 ), # MH Conga
	0xd9: ( 65,  0 ), # Hi.Timbl
	0xda: ( 66,  0 ), # LowTimbl
	0xdb: ( 74,  0 ), # L.Guiro
	0xdc: ( 73,  0 ), # S.Guiro
	0xdd: ( 82,  0 ), # Shaker
	0xde: ( 70,  0 ), # Maracas
	0xdf: ( 45,  0 ), # MidTom 2
	0xe0: ( 75,  0 ), # Claves
	0xe1: ( 56,  0 ), # Cowbell
	0xe2: ( 67,  0 ), # Hi.Agogo
	0xe3: ( 68,  0 ), # LowAgogo
	0xe4: ( 76,  0 ), # Hi.W.Blk
	0xe5: ( 77,  0 ), # LowW.Blk
	0xe6: ( 72,  0 ), # LL.Whisl
	0xe7: ( 71,  0 ), # Sh.Whisl

	0xe9: ( 39, 24 ), # HandClap
	0xea: ( 39,  0 ), # 909 Clap
	0xeb: ( 31,  0 ), # Sticks
	0xec: ( 37,  0 ), # Sd.Stick
	0xed: ( 58,  0 ), # Vib-slap

	0xef: ( 25,  0 ), # Snr.Roll
	0xf0: ( 41, 25 ), # 808 LT2
	0xf1: ( 43, 25 ), # 808 LT1
	0xf2: ( 45, 25 ), # 808 MT2
	0xf3: ( 47, 25 ), # 808 MT1
	0xf4: ( 48, 25 ), # 808 HT2
	0xf5: ( 50, 25 ), # 808 HT1
	0xf6: ( 55, 56 ), # HeartBt.
	0xf7: ( 84,  0 ), # BellTree
	0xf8: ( 83,  0 ), # Jng.Bell
	0xf9: ( 52,  0 ), # Chin.Cym
	0xfa: ( 87,  0 ), # Op.Surdo
	0xfb: ( 86,  0 ), # Mt.Surdo
	0xfc: ( 38, 16 ), # Power S1
	0xfd: ( 36, 16 ), # Power K1
	0xfe: ( 45, 16 ), # PowMTom2
	0xff: ( 36,  0 )  # Std.1 K1
}

#-----------------------------------------------------------

patch_ex_map = {}

#-----------------------------------------------------------

class ParserEvent:
	def __init__( self, event_type: int, offset: int, time: int, param1: int, param2: int = None ):
		self.type = event_type
		self.offset = offset
		self.time = time

		if   event_type == EventTypes.CC:
			self.control = param1
			self.value = param2
		elif event_type == EventTypes.NOTE_OFF:
			self.note = param1
			self.velocity = min( param2, 127 )
		elif event_type == EventTypes.NOTE_ON:
			self.note = param1
			self.velocity = min( param2, 127 )
		elif event_type == EventTypes.PROGRAM:
			self.control = 0
			self.value = param1
			self.program = min( param2, 127 )
		elif event_type == EventTypes.WHEEL:
			self.pitch = param1
		elif event_type == EventTypes.TEMPO:
			self.tempo = param1
		elif event_type == EventTypes.TEMPO_FADE:
			self.fade_time = param1
			self.target = param2
		elif event_type == EventTypes.SYSEX:
			self.data = param1

#-----------------------------------------------------------

class ParserTrack:
	def __init__( self, channel: int ):
		self.events			: List[ParserEvent] = []
		self.detour_remain	= 0
		self.ret_pos		= 0
		self.time_at		= 0
		self.channel		= channel
		self.coarse_tune	= 0
		self.fine_tune		= 0
		self.track_tune		= 0
		self.drum_active	= None
		self.patch_bank		= 0
		self.patch			= None

	def sort_events_by_time( self ) -> None:
		self.events.sort( key = lambda x: x.time )

#-----------------------------------------------------------

class Parser:
	def __init__( self ):
		self.next_channel		= 0
		self.tracks				: List[ParserTrack] = []
		self.next_empty_drum	= 72

	def add_track( self ) -> None:
		self.tracks.append( ParserTrack( self.next_channel ) )
		self.next_channel += 1

	def add_drum( self, sample ) -> None:
		if self.next_empty_drum > 100:
			sys.exit( "Exceeded drum_limit" )

		if not sample in drum_ex_map:
			note = self.next_empty_drum - 72

			print( 'Translation of EX drum {:02X} is not supported yet'.format( sample ) )
			print( 'Will default to MIDI note {:d}'.format( note ) )

			drum_map[self.next_empty_drum] = ( note, 0 )
		else:
			drum_info = drum_ex_map[sample]
			drum_map[self.next_empty_drum] = drum_info

		self.next_empty_drum += 1
		

#-----------------------------------------------------------

def read_int( f: BinaryIO, width: int, signed: bool ) -> int:
	return int.from_bytes( f.read( width ), byteorder = 'big', signed = signed )

#-----------------------------------------------------------

def handle_detour( f: BinaryIO, track: ParserTrack ) -> None:
	if track.detour_remain > 0:
		track.detour_remain -= 1
		if track.detour_remain == 0:
			f.seek( track.ret_pos )

#-----------------------------------------------------------

def handle_tempo_fades( f: BinaryIO, parser: Parser, track_num: int ) -> None:
	track = parser.tracks[track_num]
	tempo = 156

	# number of tempo events encountered+generated so far
	occurrence = 0

	for event in track.events:
		if event.type == EventTypes.TEMPO:
			tempo = event.tempo
			occurrence += 1

		if event.type == EventTypes.TEMPO_FADE:
			next_tempo = None

			try:
				next_tempo = [e[1] for e in enumerate( track.events ) if e[1].type == EventTypes.TEMPO][occurrence]
			except IndexError:
				pass

			time = event.time
			fade_time = 1 if event.fade_time <= 0 else event.fade_time
			step = int( ( event.target - tempo ) / fade_time )

			if next_tempo == None:
				for i in range( event.fade_time ):
					track.events.append( ParserEvent( EventTypes.TEMPO, event.offset, time + i, tempo + ( step * i ) ) )
					occurrence += 1
					
				track.events.append( ParserEvent( EventTypes.TEMPO, event.offset, time + event.fade_time, event.target ) )
				occurrence += 1
			else:
				num_events = next_tempo.time - event.time

				for i in range( num_events ):
					track.events.append( ParserEvent( EventTypes.TEMPO, event.offset, time + i, tempo - ( step * i ) ) )
					occurrence += 1

#-----------------------------------------------------------

def parse_subseg_track( f: BinaryIO, track: ParserTrack, is_drum: bool ) -> None:
	offset = f.tell()

	cmd = read_int( f, 1, False )
	handle_detour( f, track )

	# handle sysex for normal/drum mode
	if is_drum != track.drum_active:
		track.drum_active = is_drum

		if is_drum:
			# set Part Mode to Drum1
			track.events.append( ParserEvent( 
				EventTypes.SYSEX, 0, track.time_at, ( 0x40, 0x10 | track.channel + 1, 0x15, 0x01 ) ) )
		else:
			# set Part Mode to Norm
			track.events.append( ParserEvent( 
				EventTypes.SYSEX, 0, track.time_at, ( 0x40, 0x10 | track.channel + 1, 0x15, 0x00 ) ) )

	# parse commands
	while cmd != 0:
		# delta time
		if cmd < 0x80:
			# long delta time
			if cmd >= 0x78:
				b2 = read_int( f, 1, False )
				handle_detour( f, track )
				track.time_at += ( ( cmd & 7 ) << 8 ) + b2 + 0x78
			# short delta time
			else:
				track.time_at += cmd
		# note event
		elif cmd < 0xd4:
			note   = cmd & 0x7f
			vel    = read_int( f, 1, False )
			handle_detour( f, track )
			length = read_int( f, 1, False )
			handle_detour( f, track )

			# long length
			if length >= 0xc0:
				b2 = read_int( f, 1, False )
				handle_detour( f, track )
				length = ( ( length & ~0xc0 ) << 8 ) + b2 + 0xc0

			if is_drum:
				try:
					params = drum_map[note]
				except KeyError:
					sys.exit( 'Drum {:d} is not in translation map'.format( note ) )

				if track.patch != params[1]:
					track.patch = params[1]
					track.events.append( ParserEvent(
						EventTypes.PROGRAM, offset, track.time_at, 0, track.patch ) )
				note = params[0]

			track.events.append( ParserEvent(
				EventTypes.NOTE_ON, offset, track.time_at, note, vel ) )
			track.events.append( ParserEvent(
				EventTypes.NOTE_OFF, offset, track.time_at + length, note, vel ) )
		# master tempo
		elif cmd == 0xe0:
			param1 = read_int( f, 2, False )
			track.events.append( ParserEvent(
				EventTypes.TEMPO, offset, track.time_at, param1 ) )
		# master volume
		elif cmd == 0xe1:
			param1 = read_int( f, 1, False )
			# TODO: implement
		# master tuning
		elif cmd == 0xe2:
			param1 = read_int( f, 1, False )
			# TODO: implement
		# unknown
		elif cmd == 0xe3:
			param1 = read_int( f, 1, False )
			# TODO: implement
		# master tempo fade
		elif cmd == 0xe4:
			param1 = read_int( f, 2, False )
			param2 = read_int( f, 2, False )
			track.events.append( ParserEvent(
				EventTypes.TEMPO_FADE, offset, track.time_at, param1, param2 ) )
			# TODO: implement
		# master volume fade
		elif cmd == 0xe5:
			param1 = read_int( f, 2, False )
			param2 = read_int( f, 1, False )
			# TODO: implement
		# master effect
		elif cmd == 0xe6:
			param1 = read_int( f, 1, False )
			param2 = read_int( f, 1, False )
			# TODO: implement
		# track patch+bank override
		elif cmd == 0xe8:
			if not is_drum:
				param1 = read_int( f, 1, False )
				param2 = read_int( f, 1, False )
				track.patch_bank = param1
				track.events.append( ParserEvent(
					EventTypes.PROGRAM, offset, track.time_at, param1, param2 ) )
		# subtrack volume
		elif cmd == 0xe9:
			param1 = read_int( f, 1, False )
			track.events.append( ParserEvent( EventTypes.CC, offset, track.time_at, 7, param1 ) )
		# subtrack pan
		elif cmd == 0xea:
			param1 = read_int( f, 1, False )
			track.events.append( ParserEvent( EventTypes.CC, offset, track.time_at, 10, param1 ) )
		# subtrack reverb
		elif cmd == 0xeb:
			param1 = read_int( f, 1, False )
			track.events.append( ParserEvent( EventTypes.CC, offset, track.time_at, 91, param1 ) )
		# segment track volume
		elif cmd == 0xec:
			param1 = read_int( f, 1, False )
			track.events.append( ParserEvent( EventTypes.CC, offset, track.time_at, 11, param1 ) )
		# subtrack coarse tune
		elif cmd == 0xed:
			track.coarse_tune = PITCH_STEP_COARSE * read_int( f, 1, True )
			track.events.append( ParserEvent(
				EventTypes.WHEEL, offset, track.time_at,
				track.coarse_tune + track.fine_tune + track.track_tune ) )
		# subtrack fine tune
		elif cmd == 0xee:
			track.coarse_tune = PITCH_STEP_FINE * read_int( f, 1, True )
			track.events.append( ParserEvent(
				EventTypes.WHEEL, offset, track.time_at,
				track.coarse_tune + track.fine_tune + track.track_tune ) )
		# segment track tune
		elif cmd == 0xef:
			param1 = read_int( f, 2, True )
			track.track_tune = param1 / 100 * PITCH_STEP_COARSE
			track.events.append( ParserEvent(
				EventTypes.WHEEL, offset, track.time_at,
				track.coarse_tune + track.fine_tune + track.track_tune ) )
		# track tremolo
		elif cmd == 0xf0:
			param1 = read_int( f, 1, False )
			param2 = read_int( f, 1, False )
			param3 = read_int( f, 1, False )
			# TODO: implement
		# track tremolo speed
		elif cmd == 0xf1:
			param1 = read_int( f, 1, False )
			# TODO: implement
		# track tremolo time
		elif cmd == 0xf2:
			param1 = read_int( f, 1, False )
			# TODO: implement
		# unknown
		elif cmd == 0xf4:
			param1 = read_int( f, 1, False )
			param2 = read_int( f, 1, False )
			# TODO: implement
		# track patch set
		elif cmd == 0xf5:
			param1 = read_int( f, 1, False )

			bank_patch = patch_ex_map[param1]
			track.events.append( ParserEvent(
				EventTypes.PROGRAM, offset, track.time_at, bank_patch[0], bank_patch[1] ) )
		# track volume fade
		elif cmd == 0xf6:
			param1 = read_int( f, 2, False )
			param2 = read_int( f, 1, False )
			# TODO: implement
		# subtrack reverb type
		elif cmd == 0xf7:
			param1 = read_int( f, 1, False )
			# TODO: implement
		# jump
		elif cmd == 0xfc:
			param1 = read_int( f, 2, False )
			param2 = read_int( f, 1, False )
			# TODO: implement
		# event trigger
		elif cmd == 0xfd:
			param1 = read_int( f, 4, False )
			# TODO: implement
		# detour
		elif cmd == 0xfe:
			param1 = read_int( f, 2, False )
			param2 = read_int( f, 1, False )
			track.ret_pos = f.tell()
			f.seek( param1 )
			track.detour_remain = param2
		# unknown
		elif cmd == 0xff:
			param1 = read_int( f, 1, False )
			param2 = read_int( f, 1, False )
			param3 = read_int( f, 1, False )
			# TODO: implement

		if cmd >= 0xe0 and cmd != 0xfe:
			for i in range( cmd_len_table[cmd - 0xe0] ):
				handle_detour( f, track )

		offset = f.tell()

		cmd = read_int( f, 1, False )
		handle_detour( f, track )

#-----------------------------------------------------------

def track2midi( track: ParserTrack, m_track = mido.MidiTrack ) -> None:
	if len( track.events ) == 0:
		return

	delta_time = 0

	# set pitch bend sensitivity to +/-24 semitones

	# RPN MSB
	m_track.append( mido.Message(
		'control_change', channel = track.channel, control = 101, value = 0, time = 0 ) )
	# RPN LSB
	m_track.append( mido.Message(
		'control_change', channel = track.channel, control = 100, value = 0, time = 0 ) )
	# data entry
	m_track.append( mido.Message(
		'control_change', channel = track.channel, control = 6, value = 24, time = 0 ) )

	# convert sequence events to MIDI events

	for e in track.events:
		event_time = e.time - delta_time

		if   e.type == EventTypes.NOTE_OFF:
			m_track.append( mido.Message(
				'note_off', channel = track.channel, note = e.note, velocity = e.velocity, time = event_time ) )
		elif e.type == EventTypes.NOTE_ON:
			m_track.append( mido.Message(
				'note_on', channel = track.channel, note = e.note, velocity = e.velocity, time = event_time ) )
		elif e.type == EventTypes.CC:
			m_track.append( mido.Message(
				'control_change', channel = track.channel, control = e.control, value = e.value, time = event_time ) )
		elif e.type == EventTypes.PROGRAM:
			# bank select MSB
			m_track.append( mido.Message(
				'control_change', channel = track.channel, control = 0, value = e.value, time = event_time ) )

			m_track.append( mido.Message(
				'program_change', channel = track.channel, program = e.program, time = 0 ) )
		elif e.type == EventTypes.WHEEL:
			# clamp pitch bend range
			if e.pitch > 8191 or e.pitch < -8192:
				print( 'WARNING: pitch event at 0x{:04x} exceeds +/-24 semitones'.format( e.offset ) )

			pitch = max( min( e.pitch, 8191 ), -8192 )

			m_track.append( mido.Message(
				'pitchwheel', channel = track.channel, pitch = int( pitch ), time = event_time ) )
		elif e.type == EventTypes.TEMPO:
			m_track.append( mido.MetaMessage(
				'set_tempo', tempo = mido.bpm2tempo( e.tempo ), time = event_time ) )
		elif e.type == EventTypes.SYSEX:
			checksum = 128 - ( sum( e.data ) % 128 )
			data = ( 0x41, 0x10, 0x42, 0x12 ) + e.data + ( checksum, )
			
			m_track.append( mido.Message( 
				'sysex', data = data, time = event_time ) )

		delta_time = e.time

#-----------------------------------------------------------

def main():
	args = argparse.ArgumentParser()
	parser = Parser()

	args.add_argument(
		'-t', '--translate-drums', action = 'store_true',
		help = 'translate drum mapping to GS drum mapping' )
	args.add_argument(
		'-i', '--in', dest = 'in_file',
		help = 'BGM file name', required = True )
	args.add_argument(
		'-s', '--segment', dest = 'segment',
		type = int, choices = range( 0, 4 ),
		help = 'segment ID (0-3)', required = True )
	args.add_argument(
		'-o', '--out', dest = 'out_file',
		help = 'MIDI file name', required = True )

	args = args.parse_args()

	bin_f = open( args.in_file, 'rb' )
	mid_f = mido.MidiFile( type = 1 )
	mid_f.ticks_per_beat = 48

	# ------------------------------------------------
	# read from BGMFileInfo

	bin_f.seek( 0x14 + ( args.segment << 1 ) )

	seg_ofs = read_int( bin_f, 2, False ) << 2
	seg_pos = seg_ofs

	bin_f.seek( 0x1c )
	drums_ofs = read_int( bin_f, 2, False ) << 2
	drums_cnt = read_int( bin_f, 2, False )

	patch_ofs = read_int( bin_f, 2, False ) << 2
	patch_cnt = read_int( bin_f, 2, False )

	if seg_ofs == 0:
		sys.exit( 'Requested segment does not exist' )

	# ------------------------------------------------
	# load EX drum data

	bin_f.seek( drums_ofs )

	for i in range( drums_cnt ):
		# dummy read
		read_int( bin_f, 1, False )

		parser.add_drum( read_int( bin_f, 1, False ) )
		
		# dummy read
		read_int( bin_f, 10, False )

	# ------------------------------------------------
	# load EX patch data

	bin_f.seek( patch_ofs )

	for i in range( patch_cnt ):
		bank	= read_int( bin_f, 1, False )
		patch	= read_int( bin_f, 1, False )
		patch_ex_map[i] = ( bank, patch )

		# dummy read
		read_int( bin_f, 6, False )

	# ------------------------------------------------
	# begin track data parsing

	for i in range( 16 ):
		parser.add_track()

	while True:
		for track in parser.tracks:
			track.time_at = parser.tracks[0].time_at

		bin_f.seek( seg_pos )
		seg_pos += 4

		seg_cmd = read_int( bin_f, 2, False )

		if seg_cmd == 0:
			break

		sub_ofs = read_int( bin_f, 2, False ) << 2

		if sub_ofs == 0:
			continue
	
		sub_ofs += seg_ofs
		bin_f.seek( sub_ofs )

		for track in parser.tracks:
			track_ofs = read_int( bin_f, 2, False )

			track_flags = read_int( bin_f, 2, False )
			is_drum = track_flags & 0x0080 != 0 and args.translate_drums == True	

			if track_ofs == 0:
				continue

			track_ofs += sub_ofs

			next_track_pos = bin_f.tell()
			bin_f.seek( track_ofs )

			parse_subseg_track( bin_f, track, is_drum )
			track.sort_events_by_time()

			bin_f.seek( next_track_pos )

	for i in range( 16 ):
		track = parser.tracks[i]
		handle_tempo_fades( bin_f, parser, i )
		track.sort_events_by_time()
		
		if len( track.events ) != 0:
			m_track = mido.MidiTrack()
			mid_f.tracks.append( m_track )
			track2midi( track, m_track )

	mid_f.save( args.out_file )

#-----------------------------------------------------------

if __name__ == '__main__':
	main()
