import random
import itertools

HEADER="""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CanvasColor</key>
	<dict>
		<key>w</key>
		<string>1</string>
	</dict>
	<key>ColumnAlign</key>
	<integer>1</integer>
	<key>ColumnSpacing</key>
	<real>36</real>
	<key>CreationDate</key>
	<string>2005-08-24 01:01:05 +0100</string>
	<key>Creator</key>
	<string>Stian Soiland</string>
	<key>GraphDocumentVersion</key>
	<integer>4</integer>
	<key>GraphicsList</key>
	<array>
"""    

LINE=r"""
		<dict>
			<key>Class</key>
			<string>LineGraphic</string>
			<key>Head</key>
			<dict>
				<key>ID</key>
				<integer>%s</integer>
			</dict>
			<key>ID</key>
			<integer>%s</integer>
			<key>Labels</key>
			<array>
				<dict>
					<key>Label</key>
					<dict>
						<key>Align</key>
						<integer>0</integer>
						<key>Text</key>
						<string>{\rtf1\mac\ansicpg10000\cocoartf824\cocoasubrtf100
{\fonttbl\f0\fswiss\fcharset77 Helvetica;}
{\colortbl;\red255\green255\blue255;}
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\ql\qnatural\pardirnatural

\f0\fs24 \cf0 %s}</string>
					</dict>
					<key>LabelVisible</key>
					<string>YES</string>
					<key>Offset</key>
					<real>0.0</real>
					<key>Position</key>
					<real>0.4643804132938385</real>
				</dict>
			</array>
			<key>Points</key>
			<array>
				<string>{%s, %s}</string>
				<string>{%s, %s}</string>
			</array>
			<key>Style</key>
			<dict>
				<key>stroke</key>
				<dict>
					<key>HeadArrow</key>
					<string>StickArrow</string>
					<key>LineType</key>
					<integer>1</integer>
					<key>TailArrow</key>
					<string>0</string>
				</dict>
			</dict>
			<key>Tail</key>
			<dict>
				<key>ID</key>
				<integer>%s</integer>
			</dict>
		</dict>
"""

POINT = """
            <dict>
                <key>Bounds</key>
                <string>{{%s, %s}, {21, 21}}</string>
                <key>Class</key>
                <string>ShapedGraphic</string>
                <key>ID</key>
                <integer>%s</integer>
                <key>Shape</key>
                <string>Circle</string>
                <key>Style</key>
                <dict>
                    <key>fill</key>
                    <dict>
                        <key>Color</key>
                        <dict>
                            <key>b</key>
                            <string>0</string>
                            <key>g</key>
                            <string>0</string>
                            <key>r</key>
                            <string>0</string>
                        </dict>
                    </dict>
                    <key>shadow</key>
                    <dict>
                        <key>Draws</key>
                        <string>NO</string>
                    </dict>
                </dict>
            </dict>
"""

STARTPOINT = """            
            <dict>
                <key>Bounds</key>
                <string>{{%s, %s}, {30, 30}}</string>
                <key>Class</key>
                <string>ShapedGraphic</string>
                <key>ID</key>
                <integer>%s</integer>
                <key>Shape</key>
                <string>Circle</string>
            </dict>
"""

BOX = r"""
		<dict>
			<key>Bounds</key>
			<string>{{%s, %s}, {41, 45}}</string>
			<key>Class</key>
			<string>ShapedGraphic</string>
			<key>FitText</key>
			<string>Vertical</string>
			<key>Flow</key>
			<string>Resize</string>
			<key>FontInfo</key>
			<dict>
				<key>Font</key>
				<string>LucidaGrande</string>
				<key>Size</key>
				<real>12</real>
			</dict>
			<key>ID</key>
			<integer>%s</integer>
			<key>Shape</key>
			<string>RoundedRectangle</string>
            %s
			<key>Text</key>
			<dict>
				<key>Text</key>
				<string>{\rtf1\mac\ansicpg10000\cocoartf824\cocoasubrtf100
{\fonttbl\f0\fnil\fcharset77 LucidaGrande;}
{\colortbl;\red255\green255\blue255;}
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\qc\pardirnatural

\f0\fs24 \cf0 %s}</string>
			</dict>
		</dict>
"""

BOX_BG = """
			<key>Style</key>
			<dict>
				<key>fill</key>
				<dict>
					<key>Color</key>
					<dict>
						<key>b</key>
						<string>%s</string>
						<key>g</key>
						<string>%s</string>
						<key>r</key>
						<string>%s</string>
					</dict>
				</dict>
				<key>shadow</key>
				<dict>
					<key>Draws</key>
					<string>NO</string>
				</dict>
			</dict>
"""
        
FOOTER = """        
	</array>
	<key>GridInfo</key>
	<dict/>
	<key>GuidesLocked</key>
	<string>NO</string>
	<key>GuidesVisible</key>
	<string>YES</string>
	<key>HPages</key>
	<integer>1</integer>
	<key>ImageCounter</key>
	<integer>3</integer>
	<key>IsPalette</key>
	<string>NO</string>
	<key>Layers</key>
	<array>
		<dict>
			<key>Lock</key>
			<string>NO</string>
			<key>Name</key>
			<string>Layer 1</string>
			<key>Print</key>
			<string>YES</string>
			<key>View</key>
			<string>YES</string>
		</dict>
	</array>
	<key>LayoutInfo</key>
	<dict>
		<key>ChildOrdering</key>
		<integer>0</integer>
		<key>HierarchicalOrientation</key>
		<integer>0</integer>
		<key>LayoutType</key>
		<integer>0</integer>
		<key>Random</key>
		<string>YES</string>
		<key>Spring</key>
		<real>1.1992857456207275</real>
	</dict>
	<key>LinksVisible</key>
	<string>NO</string>
	<key>MagnetsVisible</key>
	<string>NO</string>
	<key>ModificationDate</key>
	<string>2005-08-24 11:20:27 +0100</string>
	<key>Modifier</key>
	<string>Stian Soiland</string>
	<key>ReadOnly</key>
	<string>NO</string>
	<key>RowAlign</key>
	<integer>1</integer>
	<key>RowSpacing</key>
	<real>36</real>
	<key>SheetTitle</key>
	<string>Canvas 1</string>
	<key>SmartAlignmentGuidesActive</key>
	<string>YES</string>
	<key>SmartDistanceGuidesActive</key>
	<string>YES</string>
	<key>UseEntirePage</key>
	<true/>
	<key>VPages</key>
	<integer>1</integer>
	<key>WindowInfo</key>
	<dict>
		<key>CurrentSheet</key>
		<string>0</string>
		<key>Frame</key>
		<string>{{0, 0}, {600, 800}}</string>
		<key>ShowRuler</key>
		<false/>
		<key>ShowStatusBar</key>
		<true/>
		<key>VisibleRegion</key>
		<string>{{0, 0}, {600, 800}}</string>
		<key>Zoom</key>
		<string>1</string>
	</dict>
</dict>
</plist>
"""


MIN=(50,50)
MAX=(400,400)


def random_point():
    return [min+random.random()*(max-min) for min,max in zip(MIN,MAX)]

class Graffle:
    def __init__(self):
        self.out = open("tiles.graffle", "w")
        self.out.write(HEADER)
        self.points = {}
        self._id = itertools.count(10)
    
    def new_id(self):
        return self._id.next()    
    new_id = property(new_id)    
    
    def draw(self, node, label, to_node, step):
        (id1,x1,y1) = self.draw_node(node, step)
        (id2,x2,y2) = self.draw_node(to_node, step+1)
        self.out.write(LINE % (id2, self.new_id, label, 
                               x2, y2, x1, y1, id1))

    def draw_box(self, node, step):
        if node not in self.points:
            gray = 1 - 0.07*step
            if not self.points:
                bg = ""
            else:
                bg = BOX_BG % (gray, gray, gray)
            x,y = random_point()    
            id = self.new_id
            text = node.replace("\n", "\\\n")
            self.out.write(BOX % (x,y,id, bg, text))
            self.points[node] = (id,x,y)
        return self.points[node]

    def draw_node(self, node, step):
        return self.draw_box(node, step)
        #return self.draw_point(node)
    
    def draw_point(self, node):    
        if node not in self.points:
            x,y = random_point()    
            id = self.new_id
            if not self.points:
                # First point!
                template = STARTPOINT
            else:
                template = POINT    
            self.out.write(template % (x,y,id))
            self.points[node] = (id,x,y)
        return self.points[node]

    def close(self):
        self.out.write(FOOTER)
        self.out.close()      
        self.out = None

    def __del__(self):
        if self.out:
            self.close()    


if __name__ == "__main__":
    #out = open("blapp.graffle", "w")
    #out.write(HEADER)
    #out.write(STARTPOINT % (320, 200, 14))
    #out.write(POINT % (412, 350, 15))
    #out.write(LINE % (15, 16, "south", 320, 200, 412, 350, 14))
    #out.write(FOOTER)
    g = Graffle()
    g.draw("fisk", "north", "frosk")
    g.draw("fisk", "south", "brun")
    g.draw("brun", "east", "frosk")
    g.draw("brun", "north", "stavanger")
    g.draw("stavanger", "north", "bergen")
    g.draw("bergen", "east", "brun")
    g.draw("bergen", "west", "frosk")

    
    g.close() 

