import aud
import bpy
from bpy.props import IntProperty, FloatProperty, PointerProperty
import nodeitems_utils
from nodeitems_utils import NodeItem, NodeCategory

bl_info = {
  "name": "Audio Nodes",
  "category": "Node",
}

class AudioNodeTree(bpy.types.NodeTree):
  bl_description = "Audio Node Trees"
  bl_icon = "SOUND"
  bl_idname = "AudioNodeTree"
  bl_label = "Audio node tree"

class AudioNodeSocket(bpy.types.NodeSocket):
  bl_idname = "AudioNodeSocket"
  bl_label = "Audio Node Socket"

  def draw(self, context, layout, node, x):
    layout.label(self.name)

  def draw_color(self, context, node):
    return (1, 0.5, 0, 0.5)

def connected_node(node, socket):
  for link in node.id_data.links:
    if link.to_socket == node.inputs[socket]:
      return link.from_node
  return None

def connected_node_sound(node, socket):
  node = connected_node(node, socket)
  if node == None:
    return None
  return node.get_sound()

class AudioSineNode(bpy.types.Node):
  bl_idname = "AudioSineNode"
  bl_label = "Sine"
  bl_icon = "SPEAKER"

  frequency_prop = bpy.props.FloatProperty(name="Frequency", default=440, soft_min=20, soft_max=20000)
  rate_prop = bpy.props.FloatProperty(name="Sample Rate", default=44100, soft_min=11050, soft_max=192000)
  
  def init(self, context):
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "frequency_prop")
    layout.prop(self, "rate_prop")

  def get_sound(self):
    return aud.Factory.sine(self.frequency_prop, self.rate_prop)
  
class AudioFileNode(bpy.types.Node):
  bl_idname = "AudioFileNode"
  bl_label = "Sound File"
  bl_icon = "SPEAKER"

  file_name_prop = bpy.props.StringProperty(subtype="FILE_PATH", name="File", default="//")

  def init(self, context):
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "file_name_prop")

  def get_sound(self):
    return aud.Factory(bpy.path.abspath(self.file_name_prop))
  
class AudioOutputNode(bpy.types.Node):
  bl_idname = "AudioOutputNode"
  bl_label = "Speaker"
  bl_icon = "SPEAKER"

  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
  
  def get_sound(self):
    return connected_node_sound(self, 0)
  
  def draw_buttons(self, context, layout):
    layout.context_pointer_set("audionode", self)
    layout.operator("node.play_audio")

class AudioAccumulatorNode(bpy.types.Node):
  bl_idname = "AudioAccumulatorNode"
  bl_label = "Accumulator"
  bl_icon = "SPEAKER"

  additive_prop = bpy.props.BoolProperty(name="Additive", default=False)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "additive_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.accumulate(self.additive_prop)
  
class AudioDelayNode(bpy.types.Node):
  bl_idname = "AudioDelayNode"
  bl_label = "Delay"
  bl_icon = "SPEAKER"

  time_prop = bpy.props.FloatProperty(name="Time", default=0, min=0, soft_max=10)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "time_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.delay(self.time_prop)
  
class AudioEnvelopeNode(bpy.types.Node):
  bl_idname = "AudioEnvelopeNode"
  bl_label = "Envelope"
  bl_icon = "SPEAKER"

  attack_prop = bpy.props.FloatProperty(name="Attack", default=0.005, min=0, soft_max=2)
  release_prop = bpy.props.FloatProperty(name="Release", default=0.2, min=0, soft_max=5)
  threshold_prop = bpy.props.FloatProperty(name="Threshold", default=0, min=0, soft_max=1)
  arthreshold_prop = bpy.props.FloatProperty(name="A/R Threshold", default=0.1, min=0, soft_max=1)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "attack_prop")
    layout.prop(self, "release_prop")
    layout.prop(self, "threshold_prop")
    layout.prop(self, "arthreshold_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.envelope(self.attack_prop, self.release_prop, self.threshold_prop, self.arthreshold_prop)
  
class AudioFaderNode(bpy.types.Node):
  bl_idname = "AudioFaderNode"
  bl_label = "Fader"
  bl_icon = "SPEAKER"

  start_prop = bpy.props.FloatProperty(name="Start", default=0, soft_min=0)
  length_prop = bpy.props.FloatProperty(name="Length", default=1, soft_min=0)
  inverse_prop = bpy.props.BoolProperty(name="Invert", default=False)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "start_prop")
    layout.prop(self, "length_prop")
    layout.prop(self, "inverse_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    if self.inverse_prop:
      return sound.fadeout(self.start_prop, self.length_prop)
    else:
      return sound.fadein(self.start_prop, self.length_prop)
  
class AudioHighpassNode(bpy.types.Node):
  bl_idname = "AudioHighpassNode"
  bl_label = "Highpass"
  bl_icon = "SPEAKER"

  frequency_prop = bpy.props.FloatProperty(name="Frequency", default=440, soft_min=20, soft_max=20000)
  q_prop = bpy.props.FloatProperty(name="Q Factor", default=0.5, soft_min=0, soft_max=1)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "frequency_prop")
    layout.prop(self, "q_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.highpass(self.frequency_prop, self.q_prop)
  
class AudioLimitNode(bpy.types.Node):
  bl_idname = "AudioLimitNode"
  bl_label = "Limit"
  bl_icon = "SPEAKER"

  start_prop = bpy.props.FloatProperty(name="Start", default=0, soft_min=0)
  end_prop = bpy.props.FloatProperty(name="End", default=1, soft_min=0)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "start_prop")
    layout.prop(self, "end_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.limit(self.start_prop, self.end_prop)
  
class AudioLoopNode(bpy.types.Node):
  bl_idname = "AudioLoopNode"
  bl_label = "Loop"
  bl_icon = "SPEAKER"

  loop_prop = bpy.props.IntProperty(name="Loop", default=1, soft_min=0)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "loop_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.loop(self.loop_prop)
  
class AudioLowpassNode(bpy.types.Node):
  bl_idname = "AudioLowpassNode"
  bl_label = "Lowpass"
  bl_icon = "SPEAKER"

  frequency_prop = bpy.props.FloatProperty(name="Frequency", default=440, soft_min=20, soft_max=20000)
  q_prop = bpy.props.FloatProperty(name="Q Factor", default=0.5, soft_min=0, soft_max=1)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "frequency_prop")
    layout.prop(self, "q_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.lowpass(self.frequency_prop, self.q_prop)
  
class AudioPitchNode(bpy.types.Node):
  bl_idname = "AudioPitchNode"
  bl_label = "Pitch"
  bl_icon = "SPEAKER"

  pitch_prop = bpy.props.FloatProperty(name="Pitch", default=1, soft_min=0.1, soft_max=4)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "pitch_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.pitch(self.pitch_prop)
  
class AudioSquareNode(bpy.types.Node):
  bl_idname = "AudioSquareNode"
  bl_label = "Square"
  bl_icon = "SPEAKER"

  threshold_prop = bpy.props.FloatProperty(name="Threshold", default=0, soft_min=0, soft_max=1)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "threshold_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.square(self.threshold_prop)
  
class AudioVolumeNode(bpy.types.Node):
  bl_idname = "AudioVolumeNode"
  bl_label = "Volume"
  bl_icon = "SPEAKER"

  volume_prop = bpy.props.FloatProperty(name="Volume", default=1, soft_min=0, soft_max=1)
  
  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def draw_buttons(self, context, layout):
    layout.prop(self, "volume_prop")

  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.volume(self.volume_prop)
  
class AudioJoinNode(bpy.types.Node):
  bl_idname = "AudioJoinNode"
  bl_label = "Join"
  bl_icon = "SPEAKER"

  def init(self, context):
    self.inputs.new("AudioNodeSocket", "in1")
    self.inputs.new("AudioNodeSocket", "in2")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def get_sound(self):
    sound1 = connected_node_sound(self, 0)
    sound2 = connected_node_sound(self, 1)
    if sound1 == None or sound2 == None:
      return None
    
    return sound1.join(sound2)
  
class AudioMixNode(bpy.types.Node):
  bl_idname = "AudioMixNode"
  bl_label = "Mix"
  bl_icon = "SPEAKER"

  def init(self, context):
    self.inputs.new("AudioNodeSocket", "in1")
    self.inputs.new("AudioNodeSocket", "in2")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def get_sound(self):
    sound1 = connected_node_sound(self, 0)
    sound2 = connected_node_sound(self, 1)
    if sound1 == None or sound2 == None:
      return None
    
    return sound1.mix(sound2)
  
class AudioPingPongNode(bpy.types.Node):
  bl_idname = "AudioPingPongNode"
  bl_label = "PingPong"
  bl_icon = "SPEAKER"

  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.pingpong()
  
class AudioReverseNode(bpy.types.Node):
  bl_idname = "AudioReverseNode"
  bl_label = "Reverse"
  bl_icon = "SPEAKER"

  def init(self, context):
    self.inputs.new("AudioNodeSocket", "Audio")
    self.outputs.new("AudioNodeSocket", "Audio")
  
  def get_sound(self):
    sound = connected_node_sound(self, 0)
    if sound == None:
      return None
    return sound.reverse()
  
class AudioIONodeCategory(NodeCategory):
  @classmethod
  def poll(cls, context):
    return context.space_data.tree_type == "AudioNodeTree"

class AudioFilterNodeCategory(NodeCategory):
  @classmethod
  def poll(cls, context):
    return context.space_data.tree_type == "AudioNodeTree"

class AudioSequenceNodeCategory(NodeCategory):
  @classmethod
  def poll(cls, context):
    return context.space_data.tree_type == "AudioNodeTree"

categories = [
  AudioIONodeCategory("AUDIO_IO_CATEGORY", "Input/Output", items = [
    NodeItem("AudioSineNode"),
    NodeItem("AudioFileNode"),
    NodeItem("AudioOutputNode"),
  ]),
  AudioFilterNodeCategory("AUDIO_FILTER_CATEGORY", "Filter", items = [
    # Commented out don't work with Blender < 2.8
    #NodeItem("AudioAccumulatorNode"),
    NodeItem("AudioDelayNode"),
    #NodeItem("AudioEnvelopeNode"),
    NodeItem("AudioFaderNode"),
    NodeItem("AudioHighpassNode"),
    NodeItem("AudioLimitNode"),
    NodeItem("AudioLoopNode"),
    NodeItem("AudioLowpassNode"),
    NodeItem("AudioPitchNode"),
    NodeItem("AudioSquareNode"),
    NodeItem("AudioVolumeNode"),
  ]),
  AudioSequenceNodeCategory("AUDIO_SEQUENCE_CATEGORY", "Sequence", items = [
    NodeItem("AudioJoinNode"),
    NodeItem("AudioMixNode"),
    #NodeItem("AudioPingPongNode"), not needed, as it's reverse + join
    NodeItem("AudioReverseNode"),
  ]),
]

class PlayAudioNodeOperator(bpy.types.Operator):
  bl_idname = "node.play_audio"
  bl_label = "Play Audio Node"
  
  @classmethod
  def poll(cls, context):
    return True
  
  def execute(self, context):
    sound = context.audionode.get_sound()
    if sound != None:
      aud.device().play(sound)
    return {'FINISHED'}

def register():
  bpy.utils.register_class(AudioNodeTree)
  bpy.utils.register_class(AudioNodeSocket)
  bpy.utils.register_class(AudioSineNode)
  bpy.utils.register_class(AudioFileNode)
  bpy.utils.register_class(AudioOutputNode)
  #bpy.utils.register_class(AudioAccumulatorNode)
  bpy.utils.register_class(AudioDelayNode)
  #bpy.utils.register_class(AudioEnvelopeNode)
  bpy.utils.register_class(AudioFaderNode)
  bpy.utils.register_class(AudioHighpassNode)
  bpy.utils.register_class(AudioLimitNode)
  bpy.utils.register_class(AudioLoopNode)
  bpy.utils.register_class(AudioLowpassNode)
  bpy.utils.register_class(AudioPitchNode)
  bpy.utils.register_class(AudioSquareNode)
  bpy.utils.register_class(AudioVolumeNode)
  bpy.utils.register_class(AudioJoinNode)
  bpy.utils.register_class(AudioMixNode)
  #bpy.utils.register_class(AudioPingPongNode)
  bpy.utils.register_class(AudioReverseNode)
  bpy.utils.register_class(PlayAudioNodeOperator)
  nodeitems_utils.register_node_categories("AUDIO_CATEGORIES", categories)

def unregister():
  bpy.utils.unregister_class(AudioNodeTree)
  bpy.utils.unregister_class(AudioNodeSocket)
  bpy.utils.unregister_class(AudioSineNode)
  bpy.utils.unregister_class(AudioFileNode)
  bpy.utils.unregister_class(AudioOutputNode)
  #bpy.utils.unregister_class(AudioAccumulatorNode)
  bpy.utils.unregister_class(AudioDelayNode)
  #bpy.utils.unregister_class(AudioEnvelopeNode)
  bpy.utils.unregister_class(AudioFaderNode)
  bpy.utils.unregister_class(AudioHighpassNode)
  bpy.utils.unregister_class(AudioLimitNode)
  bpy.utils.unregister_class(AudioLoopNode)
  bpy.utils.unregister_class(AudioLowpassNode)
  bpy.utils.unregister_class(AudioPitchNode)
  bpy.utils.unregister_class(AudioSquareNode)
  bpy.utils.unregister_class(AudioVolumeNode)
  bpy.utils.unregister_class(AudioJoinNode)
  bpy.utils.unregister_class(AudioMixNode)
  #bpy.utils.unregister_class(AudioPingPongNode)
  bpy.utils.unregister_class(AudioReverseNode)
  bpy.utils.unregister_class(PlayAudioNodeOperator)
  nodeitems_utils.unregister_node_categories("AUDIO_CATEGORIES")
  
if __name__ == "__main__":
  register()