# V18 visor and LED colour refinement

Requested target: the supplied concept's rounded rectangular visor with an arched upper edge, flatter lower edge and curved glass. The visor should not become a flat, sharp-cornered rectangle.

The procedural model now uses three matching curved surfaces for the white surround, dark gasket and black glass. The upper and lower outlines have different curvature. Eye and eyebrow geometry, including their morph targets, is projected onto that same surface so expressions follow the glass.

LED materials now have a black diffuse base and saturated cyan-blue emission, preventing studio illumination from bleaching the display. The browser preserves those display colours through its tone mapping. Brows have a fuller arch and tapered round-looking ends. Visor reflectivity was reduced while the ceramic helmet remains glossy.

Both hand construction blocks and the body/limb geometry remain unchanged. This pass changes the visor and display appearance, not the character's motion or voice.

Visual iteration: the first curved shell intersected the helmet at the lower centre. The glass was moved forward and its bulge reduced; its entire outline now clears the helmet. Updated front and three-quarter screenshots were inspected after the mobile tests passed. The exact flatness and curvature remain adjustable in the procedural source.

The comparison player retains V17 (the previous oval visor) below the updated version, using the same movement study so the shape and colour changes can be compared directly.

Final verification: workflow 38045575705 rebuilt both model formats, passed the mobile browser checks and rendered the refreshed 540×960, 24 fps study. Key frames at 0.5, 2.3, 4.2 and 6.5 seconds were reviewed for the visor outline, display colour and blink/pose consistency. The video uses the same diagnostic voice and estimated speech timing as V17.
