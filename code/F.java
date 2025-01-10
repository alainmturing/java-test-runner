import java.awt.*;
import java.awt.image.BufferedImage;
import java.util.Random;

public class ImageProcessor {

    public ImageProcessor() {
    }

    // Method to resize an image
    public BufferedImage resizeImage(BufferedImage inputImage, int newHeight, int newWidth) {
        BufferedImage resizedImage = new BufferedImage(newWidth, newHeight, inputImage.getType());
        Graphics2D graphics = resizedImage.createGraphics();
        graphics.drawImage(inputImage, 0, 0, newWidth, newHeight, null);
        graphics.dispose();
        return resizedImage;
    }

    // Method to crop a random section of the image
    public BufferedImage cropRandomSection(BufferedImage inputImage, int cropHeight, int cropWidth) {
        int originalWidth = inputImage.getWidth();
        int originalHeight = inputImage.getHeight();
        Random random = new Random();
        int cropX = random.nextInt(originalWidth - cropWidth);
        int cropY = random.nextInt(originalHeight - cropHeight);
        return inputImage.getSubimage(cropX, cropY, cropWidth, cropHeight);
    }

    // Method to rotate an image
    public BufferedImage rotateImage(BufferedImage inputImage, double rotationAngle) {
        int imageWidth = inputImage.getWidth();
        int imageHeight = inputImage.getHeight();
        BufferedImage rotatedImage = new BufferedImage(imageHeight, imageWidth, inputImage.getType());
        for (int y = 0; y < imageHeight; y++) {
            for (int x = 0; x < imageWidth; x++) {
                int rotatedX = (int) (imageHeight / 2 + (x - imageWidth / 2) * Math.cos(Math.toRadians(rotationAngle)) - (y - imageHeight / 2) * Math.sin(Math.toRadians(rotationAngle)));
                int rotatedY = (int) (imageWidth / 2 + (x - imageWidth / 2) * Math.sin(Math.toRadians(rotationAngle)) + (y - imageHeight / 2) * Math.cos(Math.toRadians(rotationAngle)));
                if (rotatedX >= 0 && rotatedX < imageHeight && rotatedY >= 0 && rotatedY < imageWidth) {
                    rotatedImage.setRGB(rotatedX, rotatedY, inputImage.getRGB(x, y));
                }
            }
        }
        return rotatedImage;
    }

    // Method to apply color adjustments (brightness, contrast, saturation)
    public BufferedImage applyColorAdjustments(BufferedImage inputImage, double brightnessFactor, double contrastFactor, double saturationFactor) {
        int imageWidth = inputImage.getWidth();
        int imageHeight = inputImage.getHeight();
        BufferedImage adjustedImage = new BufferedImage(imageWidth, imageHeight, inputImage.getType());

        for (int y = 0; y < imageHeight; y++) {
            for (int x = 0; x < imageWidth; x++) {
                Color originalPixel = new Color(inputImage.getRGB(x, y));

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

                Color adjustedPixel = new Color(clampValue(rgbValues[0]), clampValue(rgbValues[1]), clampValue(rgbValues[2]));
                adjustedImage.setRGB(x, y, adjustedPixel.getRGB());
            }
        }

        return adjustedImage;
    }

    // Helper method to adjust brightness
    private int adjustBrightness(int colorValue, double brightnessFactor) {
        return (int) (colorValue * (1 + brightnessFactor));
    }

    // Helper method to adjust contrast
    private int adjustContrast(int colorValue, double contrastFactor) {
        return (int) (((colorValue / 255.0 - 0.5) * (1 + contrastFactor) + 0.5) * 255);
    }

    // Helper method to adjust saturation
    private int[] adjustSaturation(int red, int green, int blue, double saturationFactor) {
        float[] hsbValues = Color.RGBtoHSB(red, green, blue, null);
        hsbValues[1] = (float) Math.min(1, Math.max(0, hsbValues[1] * (1 + saturationFactor)));
        int rgb = Color.HSBtoRGB(hsbValues[0], hsbValues[1], hsbValues[2]);
        return new int[]{(rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF};
    }

    // Helper method to clamp RGB values within the range [0, 255]
    private int clampValue(int colorValue) {
        return Math.max(0, Math.min(255, colorValue));
    }
}