package dev.duckbox.cosmetic;

import net.minecraft.client.model.ModelPart;
import net.minecraft.client.render.block.entity.model.ChestBlockModel;
import net.minecraft.client.util.math.MatrixStack;
import org.joml.Vector3f;

/** Old chest skins use the pre-1.15 Y/Z orientation. Adapt UV geometry, not their PNG pixels. */
public final class LegacyChestModel {
  public static ChestBlockModel create() {
    var root = ChestBlockModel.getSingleTexturedModelData().createModel();
    root.forEachCuboid(
        new MatrixStack(),
        (entry, path, index, cube) -> {
          for (int i = 0; i < cube.sides.length; i++) {
            var quad = cube.sides[i];
            var vertices = new ModelPart.Vertex[quad.vertices().length];
            for (int j = 0; j < vertices.length; j++) {
              var v = quad.vertices()[j];
              vertices[j] =
                  new ModelPart.Vertex(
                      new Vector3f(
                          v.pos().x,
                          cube.minY + cube.maxY - v.pos().y,
                          cube.minZ + cube.maxZ - v.pos().z),
                      v.u(),
                      v.v());
            }
            var n = quad.direction();
            cube.sides[i] = new ModelPart.Quad(vertices, new Vector3f(n.x, -n.y, -n.z));
          }
        });
    return new ChestBlockModel(root);
  }
}
