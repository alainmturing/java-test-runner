import java.awt.*;
import java.awt.image.BufferedImage;
import java.util.Random;

/**
 * A utility class for performing various image processing tasks such as resizing, cropping, rotating, 
 * and applying color adjustments.
 */
public class Solution {

    /**
     * Default constructor for ImageProcessor.
     */
    public Solution() {
    }

    /**
     * Resizes the input image to the specified width and height.
     *
     * @param inputImage The image to resize.
     * @param newHeight  The desired height of the resized image.
     * @param newWidth   The desired width of the resized image.
     * @return The resized image.
     * @throws IllegalArgumentException If the input image is null or the dimensions are invalid.
     */
    public BufferedImage resizeImage(BufferedImage inputImage, int newHeight, int newWidth) {
        if (inputImage == null || newHeight <= 0 || newWidth <= 0) {
            throw new IllegalArgumentException("Invalid input image or dimensions.");
        }

        BufferedImage resizedImage = new BufferedImage(newWidth, newHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D graphics = resizedImage.createGraphics();
        try {
            graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            graphics.drawImage(inputImage, 0, 0, newWidth, newHeight, null);
        } finally {
            graphics.dispose(); // Ensure resources are released.
        }
        return resizedImage;
    }

    /**
     * Crops a random section of the input image to the specified width and height.
     *
     * @param inputImage The image to crop.
     * @param cropHeight The height of the cropped section.
     * @param cropWidth  The width of the cropped section.
     * @return The cropped image.
     * @throws IllegalArgumentException If the input image is null, the dimensions are invalid, or the crop size exceeds the image dimensions.
     */
    public BufferedImage cropRandomSection(BufferedImage inputImage, int cropHeight, int cropWidth) {
        if (inputImage == null || cropWidth <= 0 || cropHeight <= 0) {
            throw new IllegalArgumentException("Invalid input image or crop dimensions.");
        }

        int originalWidth = inputImage.getWidth();
        int originalHeight = inputImage.getHeight();

        if (cropWidth > originalWidth || cropHeight > originalHeight) {
            throw new IllegalArgumentException("Crop dimensions exceed image dimensions.");
        }

        Random random = new Random();
        int cropX = random.nextInt(originalWidth - cropWidth + 1);
        int cropY = random.nextInt(originalHeight - cropHeight + 1);

        return inputImage.getSubimage(cropX, cropY, cropWidth, cropHeight);
    }

    /**
     * Rotates the input image by the specified angle.
     *
     * @param inputImage    The image to rotate.
     * @param rotationAngle The angle (in degrees) to rotate the image.
     * @return The rotated image.
     * @throws IllegalArgumentException If the input image is null.
     */
    public BufferedImage rotateImage(BufferedImage inputImage, double rotationAngle) {
        if (inputImage == null) {
            throw new IllegalArgumentException("Input image cannot be null.");
        }

        int imageWidth = inputImage.getWidth();
        int imageHeight = inputImage.getHeight();
        BufferedImage rotatedImage = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D graphics = rotatedImage.createGraphics();
        try {
            graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            graphics.rotate(Math.toRadians(rotationAngle), imageWidth / 2.0, imageHeight / 2.0);
            graphics.drawImage(inputImage, 0, 0, null);
        } finally {
            graphics.dispose(); // Ensure resources are released.
        }
        return rotatedImage;
    }

    /**
     * Applies brightness, contrast, and saturation adjustments to the input image.
     *
     * @param inputImage       The image to adjust.
     * @param brightnessFactor The factor to adjust brightness (-1.0 to 1.0).
     * @param contrastFactor   The factor to adjust contrast (-1.0 to 1.0).
     * @param saturationFactor The factor to adjust saturation (-1.0 to 1.0).
     * @return The adjusted image.
     * @throws IllegalArgumentException If the input image is null.
     */
    public BufferedImage applyColorAdjustments(BufferedImage inputImage, double brightnessFactor, double contrastFactor, double saturationFactor) {
        if (inputImage == null) {
            throw new IllegalArgumentException("Input image cannot be null.");
        }

        int imageWidth = inputImage.getWidth();
        int imageHeight = inputImage.getHeight();
        BufferedImage adjustedImage = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_ARGB);

        for (int y = 0; y < imageHeight; y++) {
            for (int x = 0; x < imageWidth; x++) {
                Color originalPixel = new Color(inputImage.getRGB(x, y), true);

                // Adjust brightness
                int red = adjustBrightness(originalPixel.getRed(), brightnessFactor);
                int green = adjustBrightness(originalPixel.getGreen(), brightnessFactor);
                int blue = adjustBrightness(originalPixel.getBlue(), brightnessFactor);

                // Adjust contrast
                red = adjustContrast(red, contrastFactor);
                green = adjustContrast(green, contrastFactor);
                blue = adjustContrast(blue, contrastFactor);

                // Adjust saturation
                int[] rgbValues = adjustSaturation(red, green, blue, saturationFactor);

                Color adjustedPixel = new Color(clampValue(rgbValues[0]), clampValue(rgbValues[1]), clampValue(rgbValues[2]), originalPixel.getAlpha());
                adjustedImage.setRGB(x, y, adjustedPixel.getRGB());
            }
        }
        return adjustedImage;
    }

    // Helper methods for brightness, contrast, saturation, and clamping values

    private int adjustBrightness(int colorValue, double brightnessFactor) {
        return clampValue((int) (colorValue * (1.0 + brightnessFactor)));
    }

    private int adjustContrast(int colorValue, double contrastFactor) {
        return clampValue((int) (((colorValue - 128) * contrastFactor) + 128));
    }

    private int[] adjustSaturation(int red, int green, int blue, double saturationFactor) {
        float[] hsbValues = Color.RGBtoHSB(red, green, blue, null);
        hsbValues[1] = (float) Math.max(0, Math.min(1, hsbValues[1] * (1 + saturationFactor)));
        int rgb = Color.HSBtoRGB(hsbValues[0], hsbValues[1], hsbValues[2]);
        return new int[]{(rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF};
    }

    private int clampValue(int colorValue) {
        return Math.max(0, Math.min(255, colorValue));
    }
}
