import java.awt.*;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.util.Random;

public class ImageProcessor {

    public ImageProcessor() {
    }

    // Method to resize an image
    public BufferedImage resizeImage(BufferedImage inputImage, int newHeight, int newWidth) {
        BufferedImage resizedImage = new BufferedImage(newWidth, newHeight, inputImage.getType());
        Graphics2D g2d = resizedImage.createGraphics();
        g2d.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        g2d.drawImage(inputImage, 0, 0, newWidth, newHeight, null);
        g2d.dispose();
        return resizedImage;
    }

    // Method to crop a random section of the image
    public BufferedImage cropRandomSection(BufferedImage inputImage, int cropHeight, int cropWidth) {
        Random random = new Random();
        int maxX = inputImage.getWidth() - cropWidth;
        int maxY = inputImage.getHeight() - cropHeight;
        
        if (maxX < 0 || maxY < 0) {
            throw new IllegalArgumentException("Crop dimensions are larger than image dimensions");
        }
        
        int startX = random.nextInt(maxX + 1);
        int startY = random.nextInt(maxY + 1);
        
        return inputImage.getSubimage(startX, startY, cropWidth, cropHeight);
    }

    // Method to rotate an image
    public BufferedImage rotateImage(BufferedImage inputImage, double rotationAngle) {
        double rads = Math.toRadians(rotationAngle);
        double sin = Math.abs(Math.sin(rads));
        double cos = Math.abs(Math.cos(rads));
        
        int width = inputImage.getWidth();
        int height = inputImage.getHeight();
        
        int newWidth = (int) Math.floor(width * cos + height * sin);
        int newHeight = (int) Math.floor(height * cos + width * sin);
        
        BufferedImage rotatedImage = new BufferedImage(newWidth, newHeight, inputImage.getType());
        Graphics2D g2d = rotatedImage.createGraphics();
        
        AffineTransform at = new AffineTransform();
        at.translate((newWidth - width) / 2, (newHeight - height) / 2);
        at.rotate(rads, width / 2, height / 2);
        
        g2d.setTransform(at);
        g2d.drawImage(inputImage, 0, 0, null);
        g2d.dispose();
        
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