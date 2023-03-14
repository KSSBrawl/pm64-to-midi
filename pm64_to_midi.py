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

#-----------------------------------------------------------

drum_map = {
	# STANDARD 1
	 0: ( 36,  0 ),
	 1: ( 38,  0 ),
	 2: ( 40,  0 ),
	 3: ( 42,  0 ),
	 4: ( 44,  0 ),
	 5: ( 46,  0 ),
	 6: ( 50,  0 ),
	 7: ( 48,  0 ),
	 8: ( 47,  0 ),
	 9: ( 45,  0 ),
	10: ( 43,  0 ),
	11:	( 41,  0 ),
	12: ( 49,  0 ),
	13: ( 57,  0 ),
	14: ( 61,  0 ),
	15: ( 60,  0 ),
	16: ( 79,  0 ),
	17: ( 78,  0 ),
	18: ( 54,  0 ),
	19: ( 81,  0 ),
	20: ( 80,  0 ),
	21: ( 63,  0 ),
	22: ( 64,  0 ),
	23: ( 62,  0 ),
	24: ( 65,  0 ),
	25: ( 66,  0 ),
	26: ( 74,  0 ),
	27: ( 73,  0 ),
	# ORCHESTRA
	28: ( 36, 48 ),
	29: ( 38, 48 ),
	# TR-808
	30: ( 35, 25 ),
	31: ( 36, 25 ),
	32: ( 38, 25 ),
	33: ( 40, 25 ),
	34: ( 42, 25 ),
	35: ( 46, 25 ),
	# STANDARD 1
	36: ( 51,  0 ),
	37: ( 53,  0 ),
	# ROOM
	38: ( 36,  8 ),
	39: ( 36,  8 ),
	40: ( 38,  8 ),
	# DANCE
	41: ( 35, 26 ),
	42: ( 36, 26 ),
	43: ( 38, 26 ),
	# STANDARD 1
	44: ( 69,  0 ),
	# unknown
	45: ( 26,  0 ),
	# STANDARD 1
	46: ( 75,  0 ),
	47: ( 56,  0 ),
	48: ( 67,  0 ),
	49: ( 68,  0 ),
	50: ( 76,  0 ),
	51: ( 77,  0 ),
	52: ( 72,  0 ),
	53: ( 71,  0 ),
	54: ( 82,  0 ),
	55: ( 70,  0 ),
	# ELECTRONIC
	56: ( 39, 24 ),
	# STANDARD 1
	57: ( 39,  0 ),
	58: ( 37,  0 ),
	59: ( 31,  0 ),
	60: ( 58,  0 ),
	# 61-71 appear unused
	# STANDARD 1
	72: ( 52,  0 )
}

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

#-----------------------------------------------------------

class ParserTrack:
	def __init__( self, channel: int ):
		self.events			: List[ParserEvent] = []
		self.detour_remain	= -1
		self.ret_pos		= 0
		self.time_at		= 0
		self.channel		= channel
		self.coarse_tune	= 0
		self.fine_tune		= 0
		self.track_tune		= 0
		self.patch_bank		= 0

	def sort_events_by_time( self ) -> None:
		self.events.sort( key = lambda x: x.time )

#-----------------------------------------------------------

class Parser:
	def __init__( self ):
		self.next_channel	= 0
		self.tracks			: List[ParserTrack] = []

	def add_track( self ) -> None:
		self.tracks.append( ParserTrack( self.next_channel ) )
		self.next_channel += 1

#-----------------------------------------------------------

def read_int( f: BinaryIO, width: int, signed: bool ) -> int:
	return int.from_bytes( f.read( width ), byteorder = 'big', signed = signed )

#-----------------------------------------------------------

def handle_detour( f: BinaryIO, track: ParserTrack ) -> None:
	if track.detour_remain > 0:
		track.detour_remain -= 1

	if track.detour_remain == 0:
		f.seek( track.ret_pos )
		track.detour_remain = -1

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

			try:
				step = int( ( event.target - tempo ) / event.fade_time )
			except ZeroDivisionError:
				sys.exit( "Tempo fade event cannot have fade time of zero (offset = {:08x})".format( event.offset ) )

			if next_tempo == None:
				for i in range( event.fade_time ):
					track.events.append( ParserEvent( EventTypes.TEMPO, event.offset, time + i, tempo + ( step * i ) ) )
					occurrence += 1
					
				track.events.append( ParserEvent( EventTypes.TEMPO, event.offset, time + event.fade_time, event.target ) )
				occurrence += 1
			else:
				num_events = next_tempo.time - event.time
				print( num_events )

				for i in range( num_events ):
					track.events.append( ParserEvent( EventTypes.TEMPO, event.offset, time + i, tempo - ( step * i ) ) )
					occurrence += 1

#-----------------------------------------------------------

def parse_subseg_track( f: BinaryIO, parser: Parser, track_num: int, is_drum: bool ) -> None:
	track = parser.tracks[track_num]

	offset = f.tell()
	cmd = read_int( f, 1, False )
	handle_detour( f, track )

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
		# note
		elif cmd < 0xd4:
			note	= cmd & 0x7f
			vel		= read_int( f, 1, False )
			handle_detour( f, track )
			length	= read_int( f, 1, False )
			handle_detour( f, track )

			if length >= 0xc0:
				b2 = read_int( f, 1, False )
				handle_detour( f, track )
				length = ( ( length & ~0xc0 ) << 8 ) + b2 + 0xc0

			if is_drum:
				note = drum_map[note][0]

			track.events.append( ParserEvent( EventTypes.NOTE_ON, offset, track.time_at, note, vel ) )
			track.events.append( ParserEvent( EventTypes.NOTE_OFF, offset, track.time_at + length, note, vel ) )
		# master tempo
		elif cmd == 0xe0:
			param1 = read_int( f, 2, False )
			track.events.append( ParserEvent( EventTypes.TEMPO, offset, track.time_at, param1 ) )
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
			track.events.append( ParserEvent( EventTypes.TEMPO_FADE, offset, track.time_at, param1, param2 ) )
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
		# track patch+bank set
		elif cmd == 0xe8:
			param1 = read_int( f, 1, False )
			param2 = read_int( f, 1, False )
			track.patch_bank = param1
			track.events.append( ParserEvent( EventTypes.PROGRAM, offset, track.time_at, param1, param2 ) )
		# subtrack volume
		elif cmd == 0xe9:
			param1 = read_int( f, 1, False )
			track.events.append( ParserEvent( EventTypes.CC, offset, track.time_at, 7, param1 ) )
		# subtrack pan
		elif cmd == 0xea:
			param1 = read_int( f, 1, False )
			track.events.append( ParserEvent( EventTypes.CC, offset, track.time_at, 10, param1 ) )
		# subtrack reverb event_time ) )
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
			track.events.append( ParserEvent(
				EventTypes.PROGRAM, offset, track.time_at, track.patch_bank, param1 ) )
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

		if cmd >= 0xe0:
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
			m_track.append( mido.Message(
				'pitchwheel', channel = track.channel, pitch = int( e.pitch ), time = event_time ) )
		elif e.type == EventTypes.TEMPO:
			m_track.append( mido.MetaMessage(
				'set_tempo', tempo = mido.bpm2tempo( e.tempo ), time = event_time ) )

		delta_time = e.time

#-----------------------------------------------------------

def main():
	args = argparse.ArgumentParser()

	args.add_argument(
		'-t', '--translate_drums',
		action = 'store_true',
		help = 'translate drum mapping to GS drum mapping' )
	args.add_argument(
		'-i', '--in',
		dest = 'in_file',
		help = 'BGM file name',
		required = True )
	args.add_argument(
		'-s', '--segment',
		dest = 'segment',
		type = int,
		choices = range( 0, 4 ),
		help = 'segment ID (0-3)',
		required = True )
	args.add_argument(
		'-o', '--out',
		dest = 'out_file',
		help = 'MIDI file name',
		required = True )

	args = args.parse_args()

	bin_f = open( args.in_file, 'rb' )
	mid_f = mido.MidiFile( type = 1 )
	mid_f.ticks_per_beat = 48

	bin_f.seek( 0x14 + ( args.segment << 1 ) )
	seg_ofs = read_int( bin_f, 2, False ) << 2
	seg_pos = seg_ofs

	if seg_ofs == 0:
		sys.exit( 'Requested segment does not exist' )

	parser = Parser()

	# TODO: only generate the number of tracks the song uses
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

		for i in range( 16 ):
			track = parser.tracks[i]

			track_ofs = read_int( bin_f, 2, False ) + sub_ofs

			track_flags = read_int( bin_f, 2, False )
			is_drum = track_flags & 0x0080 != 0 and args.translate_drums == True	

			if track_ofs == 0:
				continue

			next_track_pos = bin_f.tell()
			bin_f.seek( track_ofs )

			parse_subseg_track( bin_f, parser, i, is_drum )
			track.sort_events_by_time()

			bin_f.seek( next_track_pos )

	for i in range( 16 ):
		track = parser.tracks[i]
		handle_tempo_fades( bin_f, parser, i )
		track.sort_events_by_time()
		
		m_track = mido.MidiTrack()
		mid_f.tracks.append( m_track )
		track2midi( track, m_track )

	mid_f.save( args.out_file )

#-----------------------------------------------------------

if __name__ == '__main__':
	main()
