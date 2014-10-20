require 'base64'
require 'sass'
require 'image_optim'
         
module Sass::Script::Functions
    def font64(font)
        assert_type font, :String

        # compute file/path/extension
        
        base_path = '../../../' # from the current directory /app/styles/sass/helpers/

        root = File.expand_path(base_path, __FILE__)
        path = font.to_s[1, font.to_s.length-2]
        fullpath = File.expand_path(path, root)
        absname = File.expand_path(fullpath)
        ext = File.extname(path)

        if ext.index(%r{\.(?:ttf)}) != nil
            mime = 'font/truetype'
        end
        if ext.index(%r{\.(?:eot)}) != nil
            mime = 'font/opentype'
        end
        if ext.index(%r{\.(?:wof)}) != nil
            mime = 'application/x-font-woff'
        end

        file = File.open(fullpath, 'rb')
        text = file.read
        file.close

        text_b64 = Base64.encode64(text).gsub(/\r/,'').gsub(/\n/,'')
        contents = 'url(data:' + mime + ';base64,' + text_b64 + ')'

        Sass::Script::String.new(contents)
    end

    def url64(image)
        assert_type image, :String

        # compute file/path/extension
        
        base_path = '../../../' # from the current directory /app/styles/sass/helpers/

        root = File.expand_path(base_path, __FILE__)
        path = image.to_s[1, image.to_s.length-2]
        fullpath = File.expand_path(path, root)
        absname = File.expand_path(fullpath)
        ext = File.extname(path)

        # optimize image if it's a gif, jpg, png
        if ext.index(%r{\.(?:gif|jpg|png)}) != nil
            # homebrew link to pngcrush is outdated so need to avoid pngcrush for now
            # also homebrew doesn't support pngout so we ignore that too!
            # The following links show the compression settings...
            # https://github.com/toy/image_optim/blob/master/lib/image_optim/worker/advpng.rb
            # https://github.com/toy/image_optim/blob/master/lib/image_optim/worker/optipng.rb
            # https://github.com/toy/image_optim/blob/master/lib/image_optim/worker/jpegoptim.rb
            image_optim = ImageOptim.new(:pngcrush => false, :pngout => false, :advpng => {:level => 4}, :optipng => {:level => 7}, :jpegoptim => {:max_quality => 1}) 
            
            # we can lose the ! and the method will save the image to a temp directory, otherwise it'll overwrite the original image
            image_optim.optimize_image!(fullpath)
        end

        # base64 encode the file
        file = File.open(fullpath, 'rb') # read mode & binary mode
        text = file.read
        file.close

        text_b64 = Base64.encode64(text).gsub(/\r/,'').gsub(/\n/,'')
        contents = 'url(data:image/' + ext[1, ext.length-1] + ';base64,' + text_b64 + ')'

        Sass::Script::String.new(contents)
    end

    declare :url64, :args => [:string]
end