import org.junit.jupiter.api.Test;

import java.awt.image.BufferedImage;

import static org.junit.jupiter.api.Assertions.*;

public class MainTest {

    private final Main imageProcessor = new Main();

    @Test
    void testResizeImage_positiveCase() {
        BufferedImage inputImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_ARGB);
        BufferedImage result = imageProcessor.resizeImage(inputImage, 50, 50);
        assertNotNull(result, "Resized image should not be null");
        assertEquals(50, result.getWidth(), "Width should be resized correctly");
        assertEquals(50, result.getHeight(), "Height should be resized correctly");
    }

    @Test
    void testResizeImage_nullInput() {
        assertThrows(IllegalArgumentException.class, () -> imageProcessor.resizeImage(null, 50, 50),
                "Should throw IllegalArgumentException for null input image");
    }

    @Test
    void testResizeImage_invalidDimensions() {
        BufferedImage inputImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_ARGB);
        assertThrows(IllegalArgumentException.class, () -> imageProcessor.resizeImage(inputImage, -10, 50),
                "Should throw IllegalArgumentException for negative height");
        assertThrows(IllegalArgumentException.class, () -> imageProcessor.resizeImage(inputImage, 50, -10),
                "Should throw IllegalArgumentException for negative width");
    }

    @Test
    void testCropRandomSection_positiveCase() {
        BufferedImage inputImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_ARGB);
        BufferedImage result = imageProcessor.cropRandomSection(inputImage, 50, 50);
        assertNotNull(result, "Cropped image should not be null");
        assertEquals(50, result.getWidth(), "Width should match crop width");
        assertEquals(50, result.getHeight(), "Height should match crop height");
    }

    @Test
    void testCropRandomSection_invalidDimensions() {
        BufferedImage inputImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_ARGB);
        assertThrows(IllegalArgumentException.class, () -> imageProcessor.cropRandomSection(inputImage, 150, 50),
                "Should throw IllegalArgumentException for crop height greater than image height");
        assertThrows(IllegalArgumentException.class, () -> imageProcessor.cropRandomSection(inputImage, 50, 150),
                "Should throw IllegalArgumentException for crop width greater than image width");
    }

    @Test
    void testCropRandomSection_nullInput() {
        assertThrows(IllegalArgumentException.class, () -> imageProcessor.cropRandomSection(null, 50, 50),
                "Should throw IllegalArgumentException for null input image");
    }

    @Test
    void testRotateImage_positiveCase() {
        BufferedImage inputImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_ARGB);
        BufferedImage result = imageProcessor.rotateImage(inputImage, 45);
        assertNotNull(result, "Rotated image should not be null");
        assertEquals(100, result.getWidth(), "Width should remain the same");
        assertEquals(100, result.getHeight(), "Height should remain the same");
    }

    @Test
    void testRotateImage_nullInput() {
        assertThrows(IllegalArgumentException.class, () -> imageProcessor.rotateImage(null, 45),
                "Should throw IllegalArgumentException for null input image");
    }

    @Test
    void testApplyColorAdjustments_positiveCase() {
        BufferedImage inputImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_ARGB);
        BufferedImage result = imageProcessor.applyColorAdjustments(inputImage, 0.1, 0.2, 0.3);
        assertNotNull(result, "Adjusted image should not be null");
        assertEquals(100, result.getWidth(), "Width should remain the same");
        assertEquals(100, result.getHeight(), "Height should remain the same");
    }

    @Test
    void testApplyColorAdjustments_nullInput() {
        assertThrows(IllegalArgumentException.class, () -> imageProcessor.applyColorAdjustments(null, 0.1, 0.2, 0.3),
                "Should throw IllegalArgumentException for null input image");
    }

    @Test
    void testApplyColorAdjustments_edgeCases() {
        BufferedImage inputImage = new BufferedImage(1, 1, BufferedImage.TYPE_INT_ARGB);
        BufferedImage result = imageProcessor.applyColorAdjustments(inputImage, 1.0, 1.0, 1.0);
        assertNotNull(result, "Adjusted image should not be null");
        assertEquals(1, result.getWidth(), "Width should remain the same for a 1x1 image");
        assertEquals(1, result.getHeight(), "Height should remain the same for a 1x1 image");
    }
}