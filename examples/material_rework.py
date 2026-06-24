from pyfea.domain.materials.manager import MaterialManager

manager = MaterialManager()
magnet_material = manager.use_material("NdFeB", grade="N55")

magnet_material.tree()
density = magnet_material.NdFeB.physical.density