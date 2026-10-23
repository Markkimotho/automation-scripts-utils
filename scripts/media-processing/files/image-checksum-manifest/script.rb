#!/usr/bin/env ruby
require 'digest'
require 'json'
require 'pathname'

if ARGV.include?('--help') || ARGV.length != 1
  puts 'Usage: ruby script.rb DIRECTORY'
  exit(ARGV.include?('--help') ? 0 : 2)
end
root = Pathname.new(ARGV.fetch(0)).expand_path
abort('Directory not found') unless root.directory?
extensions = %w[.png .jpg .jpeg .webp .gif .bmp .tif .tiff]
results = []
Dir.glob(root.join('**', '*').to_s, File::FNM_DOTMATCH).sort.each do |candidate|
  path = Pathname.new(candidate)
  next unless path.file? && !path.symlink? && extensions.include?(path.extname.downcase)
  results << { path: path.relative_path_from(root).to_s, bytes: path.size, sha256: Digest::SHA256.file(path.to_s).hexdigest }
end
puts JSON.pretty_generate(results)
